#!/bin/bash
set -e

echo "=== CosyVoice3-API ==="
echo "Model: ${MODEL_DIR}"
echo "FP16:  ${FP16}"
echo "Port:  ${PORT}"
echo "======================"

exec python -m uvicorn api.main:app \
    --host 0.0.0.0 \
    --port "${PORT}" \
    --log-level info \
    --timeout-keep-alive 65
