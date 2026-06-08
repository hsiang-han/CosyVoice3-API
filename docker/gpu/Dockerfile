FROM pytorch/pytorch:2.9.1-cuda12.8-cudnn9-devel

ARG COSYVOICE_REPO=https://github.com/FunAudioLLM/CosyVoice.git
ARG COSYVOICE_BRANCH=main

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git git-lfs sox libsox-dev ffmpeg curl \
        g++ build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Clone CosyVoice repo
RUN git clone --depth 1 -b ${COSYVOICE_BRANCH} ${COSYVOICE_REPO} cosyvoice_repo && \
    cd cosyvoice_repo && \
    git submodule update --init --recursive --depth 1

# Pin transformers to 4.51.3 (5.x breaks CosyVoice3 Qwen2 attention)
RUN pip install --no-cache-dir transformers==4.51.3

# Install CosyVoice dependencies (skip torch since base image has it)
# openai-whisper uses pkg_resources in setup.py; modern setuptools in pip's
# build isolation removes it, so we install whisper with --no-build-isolation
# using the system setuptools which still has pkg_resources
RUN pip install --no-cache-dir "setuptools<71" wheel cython "numpy<2" && \
    cd cosyvoice_repo && \
    grep -iv "torch\|torchaudio\|tensorrt\|deepspeed\|transformers\|openai-whisper\|onnxruntime\|numpy" requirements.txt > requirements_filtered.txt && \
    pip install --no-cache-dir -r requirements_filtered.txt && \
    pip install --no-cache-dir --no-build-isolation openai-whisper==20231117 && \
    pip install --no-cache-dir modelscope "onnxruntime-gpu>=1.19" huggingface_hub && \
    pip install --no-cache-dir --force-reinstall torchvision --index-url https://download.pytorch.org/whl/cu128

# Install API dependencies (numpy already pinned <2 above, don't override)
RUN pip install --no-cache-dir fastapi uvicorn[standard] python-multipart soundfile

# Copy API code
COPY api/ ./api/
COPY docker/scripts/entrypoint.sh .
RUN chmod +x entrypoint.sh

ENV MODEL_DIR=FunAudioLLM/Fun-CosyVoice3-0.5B-2512 \
    HF_ENDPOINT=https://huggingface.co \
    FP16=true \
    PORT=8080 \
    PYTHONPATH=/app/cosyvoice_repo:/app/cosyvoice_repo/third_party/Matcha-TTS \
    PYTHONUNBUFFERED=1

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=300s --retries=3 \
    CMD curl -sf http://localhost:${PORT}/health || exit 1

ENTRYPOINT ["./entrypoint.sh"]
