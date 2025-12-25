# Chat Coach - Local LLM Setup Instructions

## Prerequisites
- 8GB VRAM GPU (NVIDIA recommended)
- Docker & Docker Compose
- ~5GB free disk space

## Model Download (Required)

The Qwen2.5-7B-Instruct GGUF model is required for Chat Coach local LLM.

### Option 1: Automated Script (Recommended)
```bash
./scripts/download_model.sh
ln -s llm_models/qwen2.5-7b-instruct-q4_k_m.gguf llm_models/model.gguf
```

### Option 2: Manual Download
1. Visit: https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF
2. Download: `qwen2.5-7b-instruct-q4_k_m.gguf` (Q4_K_M quantization)
3. Save to: `llm_models/qwen2.5-7b-instruct-q4_k_m.gguf`
4. Create symlink:
   ```bash
   ln -s llm_models/qwen2.5-7b-instruct-q4_k_m.gguf llm_models/model.gguf
   ```

### Option 3: Alternative Models
If Qwen doesn't work, try:
- Mistral-7B-Instruct-v0.3 GGUF Q4
- Llama-3-8B-Instruct GGUF Q4

Update `CHAT_LLM_MODEL` in `docker-compose.yml` to match filename.

## Verification
```bash
# Check model exists
ls -lh llm_models/model.gguf
# Should show ~5GB file

# Start services
docker compose up -d --build

# Check LLM service
docker logs filltheword-llm
# Should show: "llama server listening at http://0.0.0.0:8080"
```

## Troubleshooting

### Download Issues
- If HuggingFace is slow/blocked, use a download manager
- Model can be downloaded from another machine and copied to `llm_models/`

### GPU Issues
- Check: `nvidia-smi` (should show GPU and VRAM)
- If GPU not detected, llama.cpp will use CPU (slower but works)
- Reduce context size if OOM: edit `N_CTX` in docker-compose.yml

### Service Issues
- Check logs: `docker compose logs llm`
- Check API logs: `docker compose logs api | rg LLM`
- Verify model path: `docker exec filltheword-llm ls -la /models/`
