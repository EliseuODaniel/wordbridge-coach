#!/usr/bin/env bash
# Download Qwen 2.5 3B Instruct GGUF Q4_K_M
# Model size: ~1.8GB
# VRAM usage: ~2.1GB

set -e

MODEL_NAME="Qwen 2.5 3B Instruct"
FILE_NAME="qwen2.5-3b-instruct-q4_k_m.gguf"
DOWNLOAD_URL="https://huggingface.co/lmstudio-community/Qwen2.5-3B-Instruct-GGUF/resolve/main/Qwen2.5-3B-Instruct-Q4_K_M.gguf"
OUTPUT_DIR="llm_models"
OUTPUT_FILE="${OUTPUT_DIR}/${FILE_NAME}"

echo "=========================================="
echo "Downloading ${MODEL_NAME}"
echo "File: ${FILE_NAME}"
echo "Size: ~1.8GB"
echo "=========================================="

# Create directory if not exists
mkdir -p "${OUTPUT_DIR}"

# Check if file already exists
if [ -f "${OUTPUT_FILE}" ]; then
    echo "✓ File already exists: ${OUTPUT_FILE}"
    echo "Verifying integrity..."

    # Check file size (should be ~1.8GB = 1800000000 bytes)
    FILE_SIZE=$(stat -f%z "${OUTPUT_FILE}" 2>/dev/null || stat -c%s "${OUTPUT_FILE}" 2>/dev/null)
    if [ "${FILE_SIZE}" -gt 1700000000 ]; then
        echo "✓ File size looks good: $(numfmt --to=iec-i --suffix=B ${FILE_SIZE} 2>/dev/null || echo ${FILE_SIZE} bytes)"
        echo "Skipping download."
        exit 0
    else
        echo "⚠ File exists but size too small (${FILE_SIZE} bytes), re-downloading..."
        rm "${OUTPUT_FILE}"
    fi
fi

# Download with resume support
echo "Starting download (can be resumed if interrupted)..."
wget -c "${DOWNLOAD_URL}" -O "${OUTPUT_FILE}"

# Verify download
if [ -f "${OUTPUT_FILE}" ]; then
    FILE_SIZE=$(stat -f%z "${OUTPUT_FILE}" 2>/dev/null || stat -c%s "${OUTPUT_FILE}" 2>/dev/null)
    echo ""
    echo "=========================================="
    echo "✓ Download complete!"
    echo "File: ${OUTPUT_FILE}"
    echo "Size: $(numfmt --to=iec-i --suffix=B ${FILE_SIZE} 2>/dev/null || echo ${FILE_SIZE} bytes)"
    echo "=========================================="
else
    echo "✗ Download failed!"
    exit 1
fi
