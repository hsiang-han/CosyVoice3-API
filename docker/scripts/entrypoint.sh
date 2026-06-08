#!/bin/bash
set -e

echo "=== CosyVoice3-API ==="
echo "Model: ${MODEL_DIR}"
echo "Source: ${MODEL_SOURCE}"
echo "FP16:  ${FP16}"
echo "Port:  ${PORT}"
echo "======================"

MODEL_LOCAL_PATH="/root/.cache/models/${MODEL_DIR##*/}"

if [ -d "${MODEL_DIR}" ] && [ -f "${MODEL_DIR}/cosyvoice3.yaml" ]; then
    echo "Model found at local path: ${MODEL_DIR}"
elif [ -d "${MODEL_LOCAL_PATH}" ] && [ -f "${MODEL_LOCAL_PATH}/cosyvoice3.yaml" ]; then
    echo "Model found in cache: ${MODEL_LOCAL_PATH}"
    export MODEL_DIR="${MODEL_LOCAL_PATH}"
else
    echo "Downloading model..."
    if [ "${MODEL_SOURCE}" = "huggingface" ]; then
        echo "Source: HuggingFace (${HF_ENDPOINT})"
        pip install -q huggingface_hub 2>/dev/null || true
        python -c "
from huggingface_hub import snapshot_download
import os
snapshot_download(
    repo_id=os.environ['MODEL_DIR'],
    local_dir='${MODEL_LOCAL_PATH}',
    endpoint=os.environ.get('HF_ENDPOINT', 'https://huggingface.co'),
)
"
        export MODEL_DIR="${MODEL_LOCAL_PATH}"
    else
        echo "Source: ModelScope"
        # modelscope downloads to its own cache structure
        # Let CosyVoice handle it natively via snapshot_download
        echo "Model will be downloaded by CosyVoice on startup"
    fi
fi

exec python -m uvicorn api.main:app \
    --host 0.0.0.0 \
    --port "${PORT}" \
    --log-level info \
    --timeout-keep-alive 65
