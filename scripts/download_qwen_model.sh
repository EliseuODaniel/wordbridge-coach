#!/bin/bash
# Download Qwen2.5-7B-Instruct GGUF Q4_K_M model for llama.cpp
# Model size: ~5GB (Q4_K_M quantization)

set -e

MODEL_URL="https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/Qwen2.5-7B-Instruct-Q4_K_M.gguf"
MODEL_DIR="llm_models"
MODEL_FILE="$MODEL_DIR/model.gguf"
BACKUP_FILE="$MODEL_DIR/Phi-3-mini-4k-instruct-q4.gguf.bak"

echo "======================================="
echo "Qwen2.5-7B-Instruct Q4_K_M Downloader"
echo "======================================="
echo ""

# Create directory if not exists
mkdir -p "$MODEL_DIR"

# Backup old model if exists
if [ -f "$MODEL_FILE" ]; then
    echo "Backing up existing model to $BACKUP_FILE"
    mv "$MODEL_FILE" "$BACKUP_FILE"
fi

echo "Downloading Qwen2.5-7B-Instruct-Q4_K_M.gguf..."
echo "URL: $MODEL_URL"
echo "Target: $MODEL_FILE"
echo ""

# Download with curl (show progress)
curl -L --progress-bar \
    -H "User-Agent: Mozilla/5.0" \
    -o "$MODEL_FILE" \
    "$MODEL_URL"

echo ""
echo "Download complete!"
echo ""

# Check file size
FILE_SIZE=$(du -h "$MODEL_FILE" | cut -f1)
echo "Model file size: $FILE_SIZE"

# Expected size: ~5GB (range 4.5-5.5GB acceptable)
FILE_SIZE_BYTES=$(stat -c%s "$MODEL_FILE")
MIN_SIZE=4500000000  # 4.5GB
MAX_SIZE=6000000000  # 6GB

if [ "$FILE_SIZE_BYTES" -lt "$MIN_SIZE" ]; then
    echo "ERROR: Downloaded file too small (expected ~5GB, got $FILE_SIZE)"
    exit 1
fi

if [ "$FILE_SIZE_BYTES" -gt "$MAX_SIZE" ]; then
    echo "WARNING: Downloaded file larger than expected (expected ~5GB, got $FILE_SIZE)"
fi

echo ""
echo "======================================="
echo "Download successful!"
echo "Model saved to: $MODEL_FILE"
echo "Size: $FILE_SIZE"
echo "Ready to use with llama.cpp CUDA!"
echo "======================================="
