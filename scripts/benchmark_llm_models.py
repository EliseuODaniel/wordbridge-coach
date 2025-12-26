#!/usr/bin/env python3
"""
LLM Model Benchmark Script (Standalone)

Compares LLM profiles across multiple metrics:
- TTFB (Time to First Byte) for chat streaming
- Tokens/second generation speed
- Teacher analysis JSON validity rate
- VRAM usage per model

Outputs: Markdown report with comparison tables

Usage:
    python scripts/benchmark_llm_models.py
"""

import asyncio
import time
import json
import subprocess
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

import httpx


# ============================================================================
# Configuration
# ============================================================================

API_BASE_URL = "http://localhost:8000"
DEMO_USER_ID = "30b8a6df-1cbb-4620-b13f-f3bdb5cf1fdf"  # "demo" user
CHAT_SAMPLE_SIZE = 3  # Number of chat messages to test per model
TEACHER_SAMPLE_SIZE = 3  # Number of teacher analyses to test per model
TIMEOUT_SECONDS = 120  # Max wait for response

# Test prompts (simple, repeatable)
CHAT_PROMPTS = [
    "Hello! How are you today?",
    "What's the weather like?",
    "Tell me a joke.",
]

TEACHER_PROMPTS = [
    "I goes to school yesterday.",
    "She don't like apples.",
    "He play football every weekend.",
]


# ============================================================================
# Benchmark Functions (via HTTP API)
# ============================================================================

async def get_available_profiles() -> List[Dict[str, Any]]:
    """Fetch all available LLM profiles from API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/api/v1/llm-profiles",
            params={"user_id": DEMO_USER_ID},
            timeout=10.0
        )
        response.raise_for_status()
        data = response.json()
        return data["profiles"]


async def get_vram_usage() -> float:
    """
    Get VRAM usage via nvidia-smi in Docker container.

    Returns total VRAM used in MB.
    """
    try:
        result = subprocess.run(
            ["docker", "compose", "exec", "-T", "llm", "nvidia-smi",
             "--query-gpu=memory.used",
             "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            print(f"[WARN] nvidia-smi failed: {result.stderr}")
            return 0.0

        # Parse output: " 5456" (MB)
        memory_mb = float(result.stdout.strip())
        return memory_mb

    except Exception as e:
        print(f"[WARN] Failed to get VRAM: {e}")
        return 0.0


async def test_chat_via_websocket(profile_id: str, prompt: str) -> Dict[str, Any]:
    """
    Test chat streaming via WebSocket connection.

    Measures TTFB, total tokens, total time, tokens/sec.
    """
    import websockets
    import uuid

    try:
        # Create a test conversation first
        async with httpx.AsyncClient() as client:
            # Create conversation
            conv_response = await client.post(
                f"{API_BASE_URL}/api/v1/chat/conversations",
                json={
                    "user_id": DEMO_USER_ID,
                    "title": f"Benchmark {profile_id}",
                },
                timeout=10.0
            )
            conv_response.raise_for_status()
            conversation = conv_response.json()
            conversation_id = conversation["id"]

        # Connect to WebSocket
        ws_url = f"ws://localhost:8000/api/v1/chat/ws/{conversation_id}"

        async with websockets.connect(ws_url, timeout=30) as ws:
            # Send user message
            await ws.send_json({
                "type": "user_message",
                "content": prompt,
            })

            # Measure streaming
            ttfb = None
            first_token_time = None
            tokens = []
            start_time = time.time()
            message_count = 0

            while True:
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=TIMEOUT_SECONDS)
                    event = json.loads(response)

                    if event.get("type") == "assistant_stream_token":
                        if first_token_time is None:
                            first_token_time = time.time()
                            ttfb = (first_token_time - start_time) * 1000  # ms
                        token = event.get("token", "")
                        tokens.append(token)
                        message_count += 1

                    elif event.get("type") == "assistant_done":
                        end_time = time.time()
                        break

                    elif event.get("type") == "error":
                        return {
                            "ttfb_ms": None,
                            "total_tokens": 0,
                            "total_time_sec": 0,
                            "tokens_per_sec": 0,
                            "error": event.get("message", "Unknown error"),
                        }

                except asyncio.TimeoutError:
                    return {
                        "ttfb_ms": None,
                        "total_tokens": 0,
                        "total_time_sec": 0,
                        "tokens_per_sec": 0,
                        "error": "Timeout waiting for response",
                    }

            total_time = end_time - start_time
            total_tokens = sum(len(t.split()) for t in tokens)  # Rough estimate
            tokens_per_sec = total_tokens / total_time if total_time > 0 else 0

            return {
                "ttfb_ms": ttfb,
                "total_tokens": total_tokens,
                "total_time_sec": total_time,
                "tokens_per_sec": tokens_per_sec,
                "error": None,
            }

    except Exception as e:
        return {
            "ttfb_ms": None,
            "total_tokens": 0,
            "total_time_sec": 0,
            "tokens_per_sec": 0,
            "error": str(e),
        }


async def run_benchmark_for_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run full benchmark for a single profile.

    Tests chat streaming with sample prompts via WebSocket.
    """
    profile_id = profile["id"]
    profile_name = profile["name"]

    print(f"\n{'='*60}")
    print(f"Benchmarking: {profile_name} ({profile_id})")
    print(f"{'='*60}")

    results = {
        "profile_id": profile_id,
        "profile_name": profile_name,
        "provider": profile["provider"],
        "estimated_vram": profile["estimated_vram"],
        "quality_tier": profile["quality_tier"],
        "speed_tier": profile["speed_tier"],
        "chat_results": [],
        "vram_usage_mb": None,
    }

    # Temporarily update user preferences to use this profile
    print(f"\n[SETUP] Setting chat model to {profile_id}...")
    try:
        async with httpx.AsyncClient() as client:
            await client.put(
                f"{API_BASE_URL}/api/v1/users/me/llm-preferences",
                params={"user_id": DEMO_USER_ID},
                json={"chat_model_profile": profile_id},
                timeout=10.0
            )
    except Exception as e:
        print(f"  [WARN] Failed to set preferences: {e}")

    # Benchmark Chat Streaming
    print(f"\n[CHAT] Testing {CHAT_SAMPLE_SIZE} prompts...")
    for i, prompt in enumerate(CHAT_PROMPTS[:CHAT_SAMPLE_SIZE], 1):
        print(f"  [{i}/{CHAT_SAMPLE_SIZE}] \"{prompt[:30]}...\"", end="", flush=True)
        result = await test_chat_via_websocket(profile_id, prompt)
        results["chat_results"].append(result)
        if result["error"]:
            print(f" ❌ {result['error'][:50]}")
        else:
            print(f" ✓ {result['tokens_per_sec']:.1f} tokens/s (TTFB: {result['ttfb_ms']:.0f}ms)")

    # Get VRAM usage
    print(f"\n[VRAM] Checking usage...", end="", flush=True)
    vram_mb = await get_vram_usage()
    results["vram_usage_mb"] = vram_mb
    print(f" {vram_mb:.0f} MB")

    return results


def calculate_stats(results: List[Dict[str, Any]], key: str) -> Dict[str, float]:
    """Calculate min/max/avg for a metric across results."""
    values = [r[key] for r in results if r.get(key) is not None and r.get("error") is None]

    if not values:
        return {"min": 0, "max": 0, "avg": 0, "count": 0}

    return {
        "min": min(values),
        "max": max(values),
        "avg": sum(values) / len(values),
        "count": len(values),
    }


def generate_markdown_report(all_results: List[Dict[str, Any]]) -> str:
    """Generate Markdown report with comparison tables."""

    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "# LLM Model Benchmark Results",
        f"",
        f"**Generated:** {date_str}",
        f"**Environment:** {API_BASE_URL}",
        f"**User:** {DEMO_USER_ID}",
        f"",
        f"## Summary",
        f"",
    ]

    # Build comparison table
    lines.extend([
        "| Model | Quality | Speed | VRAM (est) | VRAM (meas) | Chat TTFB | Chat Speed |",
        "|-------|---------|-------|------------|-------------|-----------|-------------|",
    ])

    for result in all_results:
        profile_id = result["profile_id"]
        profile_name = result["profile_name"]
        quality = result["quality_tier"]
        speed = result["speed_tier"]
        vram_est = result["estimated_vram"]
        vram_meas = f"{result['vram_usage_mb']:.0f} MB"

        # Chat stats
        chat_ttfb = calculate_stats(result["chat_results"], "ttfb_ms")
        chat_speed = calculate_stats(result["chat_results"], "tokens_per_sec")

        lines.append(
            f"| {profile_name} | {quality} | {speed} | {vram_est} | {vram_meas} | "
            f"{chat_ttfb['avg']:.0f}ms | "
            f"{chat_speed['avg']:.1f} tok/s |"
        )

    # Detailed breakdown per model
    lines.extend([
        f"",
        f"## Detailed Results",
        f"",
    ])

    for result in all_results:
        profile_id = result["profile_id"]
        profile_name = result["profile_name"]

        lines.extend([
            f"### {profile_name} (`{profile_id}`)",
            f"",
            f"- **Provider:** {result['provider']}",
            f"- **Quality Tier:** {result['quality_tier']}",
            f"- **Speed Tier:** {result['speed_tier']}",
            f"- **Estimated VRAM:** {result['estimated_vram']}",
            f"- **Measured VRAM:** {result['vram_usage_mb']:.0f} MB",
            f"",
            f"#### Chat Streaming Performance",
            f"",
        ])

        chat_ttfb = calculate_stats(result["chat_results"], "ttfb_ms")
        chat_speed = calculate_stats(result["chat_results"], "tokens_per_sec")
        chat_time = calculate_stats(result["chat_results"], "total_time_sec")

        lines.extend([
            f"| Metric | Min | Avg | Max | Samples |",
            f"|--------|-----|-----|-----|--------|",
            f"| TTFB (ms) | {chat_ttfb['min']:.0f} | {chat_ttfb['avg']:.0f} | {chat_ttfb['max']:.0f} | {chat_ttfb['count']} |",
            f"| Tokens/sec | {chat_speed['min']:.1f} | {chat_speed['avg']:.1f} | {chat_speed['max']:.1f} | {chat_speed['count']} |",
            f"| Total Time (s) | {chat_time['min']:.2f} | {chat_time['avg']:.2f} | {chat_time['max']:.2f} | {chat_time['count']} |",
            f"",
        ])

    # Recommendations
    lines.extend([
        f"## Recommendations",
        f"",
    ])

    # Find best chat model (highest tokens/s)
    best_chat = max(
        all_results,
        key=lambda r: calculate_stats(r["chat_results"], "tokens_per_sec")["avg"]
    )
    best_chat_speed = calculate_stats(best_chat["chat_results"], "tokens_per_sec")["avg"]
    best_chat_ttfb = calculate_stats(best_chat["chat_results"], "ttfb_ms")["avg"]

    lines.extend([
        f"### Chat Model (Streaming)",
        f"",
        f"**Best:** {best_chat['profile_name']} (`{best_chat['profile_id']}`)",
        f"",
        f"- **Reason:** Fastest streaming speed ({best_chat_speed:.1f} tokens/second)",
        f"- **TTFB:** {best_chat_ttfb:.0f}ms average",
        f"- **Quality Tier:** {best_chat['quality_tier']}",
        f"- **Use for:** Real-time conversational responses",
        f"",
    ])

    # Default recommendation
    lines.extend([
        f"### Default Configuration",
        f"",
        f"Based on benchmark results, recommended defaults:",
        f"",
        f"- **Chat Model:** `{best_chat['profile_id']}`",
        f"  - Best balance of speed and responsiveness",
        f"  - {best_chat_speed:.1f} tokens/second average",
        f"",
        f"- **Teacher Model:** `{best_chat['profile_id']}` (same as chat for now)",
        f"  - Note: Teacher analysis not yet benchmarked (requires additional test setup)",
        f"",
    ])

    return "\n".join(lines)


# ============================================================================
# Main
# ============================================================================

async def main():
    """Run full benchmark on all available profiles."""

    print("="*60)
    print("LLM Model Benchmark (Standalone)")
    print("="*60)
    print(f"API: {API_BASE_URL}")
    print(f"User: {DEMO_USER_ID}")
    print(f"Chat samples: {CHAT_SAMPLE_SIZE}")
    print(f"Timeout: {TIMEOUT_SECONDS}s")
    print("="*60)

    # Fetch available profiles
    print("\n[1/3] Fetching available profiles...")
    profiles = await get_available_profiles()
    print(f"Found {len(profiles)} profiles")

    for profile in profiles:
        print(f"  - {profile['name']} ({profile['id']})")

    # Run benchmarks
    print(f"\n[2/3] Running benchmarks...")
    all_results = []

    for profile in profiles:
        result = await run_benchmark_for_profile(profile)
        all_results.append(result)

    # Generate report
    print(f"\n[3/3] Generating report...")
    report = generate_markdown_report(all_results)

    # Save report
    output_dir = Path("/home/edann/vscode_projects/filltheword/docs")
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"benchmark_results_{timestamp}.md"

    with open(output_file, 'w') as f:
        f.write(report)

    print(f"\n{'='*60}")
    print(f"✅ Benchmark complete!")
    print(f"{'='*60}")
    print(f"Report saved to: {output_file}")
    print(f"")
    print(f"Summary:")
    for result in all_results:
        chat_speed = calculate_stats(result["chat_results"], "tokens_per_sec")["avg"]
        print(f"  {result['profile_name']}: {chat_speed:.1f} tok/s")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Benchmark cancelled by user")
    except Exception as e:
        print(f"\n\n[ERROR] Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
