#!/bin/bash
# Download Qwen2.5-7B-Instruct GGUF model for Chat Coach

set -e

MODEL_URL="https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q4_k_m.gguf"
MODEL_FILE="llm_models/qwen2.5-7b-instruct-q4_k_m.gguf"
MODEL_LINK="llm_models/model.gguf"

# Create directory
mkdir -p llm_models

# Check if model already exists
if [ -f "$MODEL_FILE" ]; then
    echo "Model already exists: $MODEL_FILE"
    echo "Skipping download."
    exit 0
fi

echo "======================================================================="
echo "Chat Coach - Local LLM Setup"
echo "======================================================================="
echo ""
echo "Downloading Qwen2.5-7B-Instruct GGUF (Q4_K_M)..."
echo "Model size: ~5GB"
echo "This may take a while depending on your connection speed..."
echo ""
echo "Press Ctrl+C to cancel"
echo "======================================================================="
echo ""

# Download
curl -L -o "$MODEL_FILE" "$MODEL_URL"

echo ""
echo "======================================================================="
echo "Download complete!"
echo "======================================================================="
echo ""
echo "Model saved to: $MODEL_FILE"
echo "Model size: $(du -h "$MODEL_FILE" | cut -f1)"
echo ""
echo "Next steps:"
echo "1. Create symlink: ln -s $MODEL_FILE $MODEL_LINK"
echo "2. Start services: docker compose up -d --build"
echo "3. Check LLM logs: docker logs filltheword-llm"
echo ""
echo "======================================================================="
