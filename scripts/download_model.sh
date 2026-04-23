#!/bin/bash
# Download GGUF model for Chat Coach LLM with multi-file support
#
# Usage: ./scripts/download_model.sh [model_id]
#   model_id: Optional. Defaults to ggml-org/gemma-4-E4B-it-GGUF

set -euo pipefail

# Configuration
MODEL_ID="${1:-ggml-org/gemma-4-E4B-it-GGUF}"
MODEL_DIR="llm_models"
MODEL_LINK="${MODEL_DIR}/model.gguf"
PREFERRED_QUANT="q4_k_m"
FALLBACK_QUANT="q4_0"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

mkdir -p "$MODEL_DIR"

# Discover model files
log_info "Querying HuggingFace API for $MODEL_ID..."
API_URL="https://huggingface.co/api/models/${MODEL_ID}"

if ! MODEL_INFO=$(curl -fsSL "$API_URL" 2>/dev/null); then
    log_error "Failed to query HuggingFace API"
    exit 1
fi

# Extract GGUF files
MODEL_FILES=$(echo "$MODEL_INFO" | python3 -c "
import sys, json, re
data = json.load(sys.stdin)
siblings = data.get('siblings', [])
gguf = [s.get('rfilename') for s in siblings if s.get('rfilename', '').endswith('.gguf')]
for f in sorted(gguf):
    print(f)
" 2>/dev/null)

if [ -z "$MODEL_FILES" ]; then
    log_error "No GGUF files found"
    exit 1
fi

FILE_COUNT=$(echo "$MODEL_FILES" | wc -l)
log_info "Found $FILE_COUNT GGUF file(s):"
echo "$MODEL_FILES" | nl

# Select quantization
SELECTED_PATTERN=""
for quant in "$PREFERRED_QUANT" "$FALLBACK_QUANT"; do
    # Check if all parts of this quantization exist
    PATTERN=$(echo "$MODEL_FILES" | grep -i "${quant}\\.gguf$" | head -1 || true)

    if [ -n "$PATTERN" ]; then
        # Extract base pattern (e.g., "qwen2.5-7b-instruct-q4_k_m")
        if echo "$PATTERN" | grep -q "00001-of-"; then
            BASE_PATTERN=$(echo "$PATTERN" | sed 's/-00001-of-[^.]*\.gguf//')
            SELECTED_PATTERN="${BASE_PATTERN}"
            log_info "Selected: ${SELECTED_PATTERN} (quantization: ${quant})"
            break
        else
            SELECTED_PATTERN=$(echo "$PATTERN" | sed 's/\.gguf$//')
            log_info "Selected: ${SELECTED_PATTERN} (quantization: ${quant}, single file)"
            break
        fi
    fi
done

if [ -z "$SELECTED_PATTERN" ]; then
    log_warn "Preferred quantizations not found, using first available"
    FIRST_FILE=$(echo "$MODEL_FILES" | head -1)
    SELECTED_PATTERN=$(echo "$FIRST_FILE" | sed 's/-00001-of-[^.]*\.gguf$//' | sed 's/\.gguf$//')
    log_info "Selected: ${SELECTED_PATTERN} (fallback)"
fi

# Find all parts for this quantization
FILES_TO_DOWNLOAD=$(echo "$MODEL_FILES" | grep -i "^${SELECTED_PATTERN}" || echo "$SELECTED_PATTERN.gguf")

PART_COUNT=$(echo "$FILES_TO_DOWNLOAD" | wc -l)
log_info "Will download $PART_COUNT file(s):"
echo "$FILES_TO_DOWNLOAD" | nl

# Check if already downloaded and valid
ALL_VALID=true
for file in $FILES_TO_DOWNLOAD; do
    LOCAL_PATH="${MODEL_DIR}/${file}"
    if [ ! -f "$LOCAL_PATH" ]; then
        ALL_VALID=false
        break
    fi

    # Validate
    SIZE=$(stat -c%s "$LOCAL_PATH" 2>/dev/null || echo 0)
    MAGIC=$(head -c4 "$LOCAL_PATH" 2>/dev/null || echo "")

    if [ "$MAGIC" != "GGUF" ] || [ "$SIZE" -lt 100000000 ]; then
        ALL_VALID=false
        break
    fi
done

if [ "$ALL_VALID" = true ] && [ -n "$(ls ${MODEL_DIR}/${SELECTED_PATTERN}* 2>/dev/null)" ]; then
    log_info "All files already downloaded and validated"

    # Create symlink to first part
    FIRST_FILE=$(echo "$FILES_TO_DOWNLOAD" | head -1)
    ln -sf "$FIRST_FILE" "$MODEL_LINK"
    log_info "Symlink ready: $MODEL_LINK"

    # Show total size
    TOTAL_SIZE=$(du -sh ${MODEL_DIR}/${SELECTED_PATTERN}* 2>/dev/null | awk '{sum+=$1} END {print sum " (total)"}')
    log_info "Total size: $(du -sh ${MODEL_DIR}/${SELECTED_PATTERN}* | awk '{s+=$1} END {print s}')"

    exit 0
fi

# Download files
echo ""
echo "======================================================================="
echo "Chat Coach - Local LLM Setup"
echo "======================================================================="
echo ""
echo "Model: $MODEL_ID"
echo "Files: $PART_COUNT file(s)"
echo "Total size: Expected 5-6 GB"
echo ""
echo "Press Ctrl+C to cancel"
echo "======================================================================="
echo ""

for file in $FILES_TO_DOWNLOAD; do
    LOCAL_PATH="${MODEL_DIR}/${file}"
    DOWNLOAD_URL="https://huggingface.co/${MODEL_ID}/resolve/main/${file}?download=true"

    log_info "Downloading: $file"
    log_info "URL: $DOWNLOAD_URL"

    if [ -f "$LOCAL_PATH" ]; then
        # Validate existing
        SIZE=$(stat -c%s "$LOCAL_PATH" 2>/dev/null || echo 0)
        MAGIC=$(head -c4 "$LOCAL_PATH" 2>/dev/null || echo "")

        if [ "$MAGIC" = "GGUF" ] && [ "$SIZE" -gt 100000000 ]; then
            log_warn "File already valid, skipping: $file"
            continue
        else
            log_warn "Removing invalid file: $file"
            rm -f "$LOCAL_PATH"
        fi
    fi

    # Download with retry
    if ! curl -fL --retry 3 --retry-delay 5 \
        -o "${LOCAL_PATH}.part" \
        "$DOWNLOAD_URL"; then
        log_error "Download failed: $file"
        rm -f "${LOCAL_PATH}.part"
        exit 1
    fi

    # Validate downloaded file
    SIZE=$(stat -c%s "${LOCAL_PATH}.part" 2>/dev/null || echo 0)
    MAGIC=$(head -c4 "${LOCAL_PATH}.part" 2>/dev/null || echo "")

    if [ "$MAGIC" != "GGUF" ]; then
        log_error "Invalid GGUF file: $file"
        rm -f "${LOCAL_PATH}.part"
        exit 1
    fi

    if [ "$SIZE" -lt 100000000 ]; then
        log_error "File too small: $file (${SIZE} bytes)"
        rm -f "${LOCAL_PATH}.part"
        exit 1
    fi

    mv "${LOCAL_PATH}.part" "$LOCAL_PATH"
    log_info "✓ Downloaded: $file ($(du -h "$LOCAL_PATH" | cut -f1))"
done

# Create symlink to first part
FIRST_FILE=$(echo "$FILES_TO_DOWNLOAD" | head -1)
ln -sf "$FIRST_FILE" "$MODEL_LINK"

echo ""
echo "======================================================================="
echo "Download Complete!"
echo "======================================================================="
echo ""
echo -e "${GREEN}✓${NC} Files: $PART_COUNT"
echo -e "${GREEN}✓${NC} Total size: $(du -sh ${MODEL_DIR}/${SELECTED_PATTERN}* | awk '{s+=$1} END {print s}')"
echo -e "${GREEN}✓${NC} GGUF headers validated"
echo -e "${GREEN}✓${NC} Symlink: $MODEL_LINK -> $FIRST_FILE"
echo ""
echo "Next steps:"
echo "1. Start LLM: docker compose up -d llm"
echo "2. Check logs: docker compose logs -f llm"
echo "3. Test Chat Coach: http://localhost:3007/?mode=chat"
echo ""
echo "======================================================================="
