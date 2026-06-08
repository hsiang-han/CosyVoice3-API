FROM nvcr.io/nvidia/cuda:12.8.1-cudnn-runtime-ubuntu22.04

ARG PYTHON_VERSION=3.10
ARG COSYVOICE_REPO=https://github.com/FunAudioLLM/CosyVoice.git
ARG COSYVOICE_BRANCH=main

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python${PYTHON_VERSION} python${PYTHON_VERSION}-venv python${PYTHON_VERSION}-dev \
        python3-pip git git-lfs sox libsox-dev ffmpeg curl && \
    ln -sf /usr/bin/python${PYTHON_VERSION} /usr/bin/python3 && \
    ln -sf /usr/bin/python${PYTHON_VERSION} /usr/bin/python && \
    python -m pip install --upgrade pip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Clone CosyVoice repo
RUN git clone --depth 1 -b ${COSYVOICE_BRANCH} ${COSYVOICE_REPO} cosyvoice_repo && \
    cd cosyvoice_repo && \
    git submodule update --init --recursive --depth 1

# Install PyTorch with CUDA 12.8
RUN pip install --no-cache-dir torch torchaudio --index-url https://download.pytorch.org/whl/cu128

# Install CosyVoice dependencies (pynini may fail, it's optional for text normalization)
RUN cd cosyvoice_repo && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir modelscope onnxruntime-gpu

# Install API dependencies
RUN pip install --no-cache-dir fastapi uvicorn[standard] python-multipart numpy soundfile

# Copy API code
COPY api/ ./api/
COPY docker/scripts/entrypoint.sh .
RUN chmod +x entrypoint.sh

ENV MODEL_DIR=FunAudioLLM/Fun-CosyVoice3-0.5B-2512 \
    FP16=true \
    PORT=8080 \
    PYTHONPATH=/app/cosyvoice_repo:/app/cosyvoice_repo/third_party/Matcha-TTS \
    PYTHONUNBUFFERED=1

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=180s --retries=3 \
    CMD curl -sf http://localhost:${PORT}/health || exit 1

ENTRYPOINT ["./entrypoint.sh"]
