#!/bin/bash
# Download Piper TTS models for WordBridge Coach.
set -e

echo "🎵 Downloading Piper TTS models..."

# Create models directory
mkdir -p /models

# Model definitions (correct URLs for existing models)
declare -A MODELS=(
    [en]="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx"
    [fr]="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx"
    # Note: es and pt models don't have medium versions in v1.0.0, using low quality alternatives
    [es]="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/es/es_ES/davefx/low/es_ES-davefx-low.onnx"
    [pt]="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/pt/pt_BR/edresson/low/pt_BR-edresson-low.onnx"
)

declare -A CONFIGS=(
    [en]="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json"
    [fr]="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx.json"
    [es]="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/es/es_ES/davefx/low/es_ES-davefx-low.onnx.json"
    [pt]="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/pt/pt_BR/edresson/low/pt_BR-edresson-low.onnx.json"
)

# Function to download with retry
download_with_retry() {
    local url="$1"
    local output="$2"
    local max_retries=3
    local retry=0

    while [ $retry -lt $max_retries ]; do
        if curl -L --silent --show-error --fail --output "$output" "$url"; then
            echo "✅ Downloaded: $(basename "$output")"
            return 0
        else
            echo "❌ Failed to download: $url (attempt $((retry + 1))/$max_retries)"
            rm -f "$output"  # Clean up partial download
            retry=$((retry + 1))
            sleep 2
        fi
    done

    echo "❌ Failed to download after $max_retries attempts: $url"
    return 1
}

# Download models for each language
for lang in en es fr pt; do
    echo "📦 Downloading $lang model..."

    # Create language directory
    lang_dir="/models/$lang"
    mkdir -p "$lang_dir"

    # Download model and config
    model_url="${MODELS[$lang]}"
    config_url="${CONFIGS[$lang]}"

    model_file="$lang_dir/model.onnx"
    config_file="$lang_dir/model.onnx.json"

    if download_with_retry "$model_url" "$model_file"; then
        download_with_retry "$config_url" "$config_file"
    else
        echo "❌ Failed to download $lang model"
        exit 1
    fi
done

echo ""
echo "🎉 All models downloaded successfully!"
echo ""
echo "📁 Models directory structure:"
find /models -type f -name "*.onnx*" | sort
echo ""
echo "💾 Total size:"
du -sh /models
echo ""
echo "🚀 TTS service ready to generate real audio!"
