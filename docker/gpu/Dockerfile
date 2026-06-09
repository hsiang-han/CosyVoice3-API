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

# Install CosyVoice dependencies explicitly (no grep filtering)
# Only override: torch/torchaudio (base image), numpy (pin 1.x), transformers (pin 4.51.3),
# tensorrt/deepspeed (not needed for inference), onnxruntime-gpu (need >=1.19 for cuDNN 9)
RUN pip install --no-cache-dir "setuptools<71" wheel cython "numpy==1.26.4" && \
    pip install --no-cache-dir \
        conformer==0.3.2 \
        diffusers==0.29.0 \
        fastapi==0.115.6 \
        fastapi-cli==0.0.4 \
        gdown==5.1.0 \
        gradio==5.4.0 \
        grpcio==1.57.0 \
        grpcio-tools==1.57.0 \
        hydra-core==1.3.2 \
        "HyperPyYAML==1.2.3" \
        inflect==7.3.1 \
        librosa==0.10.2 \
        lightning==2.2.4 \
        matplotlib==3.7.5 \
        modelscope==1.20.0 \
        networkx==3.1 \
        omegaconf==2.3.0 \
        onnx==1.16.0 \
        protobuf==4.25 \
        pyarrow==18.1.0 \
        pydantic==2.7.0 \
        pyworld==0.3.4 \
        rich==13.7.1 \
        soundfile==0.12.1 \
        tensorboard==2.14.0 \
        x-transformers==2.11.24 \
        uvicorn==0.30.0 \
        wetext==0.0.4 \
        wget==3.2 && \
    pip install --no-cache-dir --no-build-isolation openai-whisper==20231117 && \
    pip install --no-cache-dir "onnxruntime-gpu>=1.19" huggingface_hub && \
    pip install --no-cache-dir --force-reinstall torch==2.9.1 torchaudio==2.9.1 torchvision --index-url https://download.pytorch.org/whl/cu128 && \
    pip install --no-cache-dir "numpy==1.26.4"

# Install API dependencies
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
