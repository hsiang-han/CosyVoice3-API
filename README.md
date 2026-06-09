# CosyVoice3-API

[中文文档](README_zh.md)

OpenAI-compatible Text-to-Speech API powered by [CosyVoice 3](https://github.com/FunAudioLLM/CosyVoice) (Alibaba FunAudioLLM).

Zero-shot voice cloning with 3-second reference audio. Register voices once, use them forever. Supports RTX 50-series (Blackwell) GPUs.

## Features

- OpenAI-compatible `/v1/audio/speech` endpoint (JSON body)
- Zero-shot voice cloning from any reference audio
- Voice registration — clone once, use by name afterwards
- Streaming output support (`"stream": true` returns raw PCM)
- 9 languages, 18 Chinese dialects
- Supports RTX 50-series (Blackwell) and older GPUs

## Quick Start

```bash
docker run -d --gpus all --shm-size=2g \
  -p 8080:8080 \
  -v /mnt/user/appdata/cosyvoice3-api/models:/root/.cache/models \
  -e HF_ENDPOINT=https://huggingface.co \
  --name cosyvoice3-api \
  ghcr.io/hsiang-han/cosyvoice3-api:latest
```

First start downloads model files (~10GB) from HuggingFace. China users: set `HF_ENDPOINT=https://hf-mirror.com` for faster downloads.

## Usage

### Step 1: Register a voice (required for first use)

CosyVoice3 has no built-in voices. You need to register at least one voice from a reference audio:

```bash
curl -X POST http://localhost:8080/v1/voices/register \
  -F "voice_id=my_voice" \
  -F "prompt_text=这是参考音频中说的话的文字内容" \
  -F "prompt_wav=@reference.wav"
```

Registered voices persist across container restarts.

### Step 2: Generate speech

```bash
curl -X POST http://localhost:8080/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"input": "你好，世界", "voice": "my_voice"}' \
  --output speech.wav
```

### Streaming output

```bash
curl -X POST http://localhost:8080/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"input": "你好，世界", "voice": "my_voice", "stream": true}' \
  --output speech.pcm
```

Returns raw PCM (16-bit, mono, 24000Hz). Headers include `X-Sample-Rate`, `X-Channels`, `X-Bit-Depth`.

### Voice cloning (one-off, without registration)

```bash
curl -X POST http://localhost:8080/v1/audio/speech/clone \
  -F "input=这是克隆的声音" \
  -F "prompt_text=这是参考音频中说的话" \
  -F "prompt_wav=@reference.wav" \
  --output cloned.wav
```

### List / delete voices

```bash
curl http://localhost:8080/v1/voices

curl -X DELETE http://localhost:8080/v1/voices/my_voice
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/audio/speech` | POST | Text-to-speech (JSON body, OpenAI-compatible) |
| `/v1/audio/speech/clone` | POST | One-off voice cloning (Form + file upload) |
| `/v1/voices/register` | POST | Register a voice from reference audio |
| `/v1/voices/{voice_id}` | DELETE | Delete a registered voice |
| `/v1/voices` | GET | List registered voices |
| `/v1/models` | GET | List models |
| `/health` | GET | Health check |
| `/docs` | GET | Swagger documentation |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| MODEL_DIR | FunAudioLLM/Fun-CosyVoice3-0.5B-2512 | HuggingFace model ID or local path |
| HF_ENDPOINT | https://huggingface.co | HuggingFace mirror (China: https://hf-mirror.com) |
| FP16 | true | Half-precision inference. Reduces VRAM ~50% |

## Hardware Requirements

- NVIDIA GPU with 4GB+ VRAM (FP16) or 8GB+ (FP32)
- NVIDIA driver 550+ (Ampere/Ada) or 570+ (Blackwell RTX 50-series)
- Docker with NVIDIA Container Toolkit

## Credits

- [CosyVoice](https://github.com/FunAudioLLM/CosyVoice) by Alibaba FunAudioLLM — the model and inference framework

## License

Apache-2.0 (same as upstream CosyVoice)
