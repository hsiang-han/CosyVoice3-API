# CosyVoice3-API

[English](README.md) | [中文](README_zh.md)

OpenAI-compatible Text-to-Speech API powered by [CosyVoice 3](https://github.com/FunAudioLLM/CosyVoice) (Alibaba FunAudioLLM).

No extra services — just the model served via FastAPI with an OpenAI-compatible endpoint. Supports built-in voices, instruction-based control, and zero-shot voice cloning.

## What this adds

The official CosyVoice repo requires manual setup and has no Docker entrypoint for production use. This project adds:
- Auto-start API server on container launch
- OpenAI-compatible `/v1/audio/speech` endpoint
- Zero-shot voice cloning endpoint `/v1/audio/speech/clone`
- Environment variables for GPU/memory control
- Unraid Community Applications template

## Quick Start

```bash
docker run -d --gpus all --shm-size=2g \
  -p 8080:8080 \
  -v /path/to/models:/root/.cache/modelscope/hub \
  ghcr.io/hsiang-han/cosyvoice3-api:latest
```

First start downloads the model (~2GB).

## Usage

### Text-to-Speech (OpenAI-compatible)

```bash
curl -X POST http://localhost:8080/v1/audio/speech \
  -F "input=你好，世界" \
  -F "voice=中文女" \
  --output speech.wav
```

### With instruction control

```bash
curl -X POST http://localhost:8080/v1/audio/speech \
  -F "input=今天天气真好" \
  -F "voice=中文女" \
  -F "instruct_text=用开心的语气说" \
  --output happy.wav
```

### Voice cloning

```bash
curl -X POST http://localhost:8080/v1/audio/speech/clone \
  -F "input=这是克隆的声音" \
  -F "prompt_text=这是参考音频中说的话" \
  -F "prompt_wav=@reference.wav" \
  --output cloned.wav
```

### List available voices

```bash
curl http://localhost:8080/v1/voices
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_DIR` | `FunAudioLLM/Fun-CosyVoice3-0.5B-2512` | ModelScope model ID |
| `FP16` | `true` | Half-precision inference. Reduces VRAM ~50%. |
| `PORT` | `8080` | API server port |

## VRAM Usage

| Config | Estimated VRAM |
|--------|---------------|
| FP16=true (default) | ~3-4GB |
| FP16=false | ~6-8GB |

## Unraid Install

1. Add template repo: `https://github.com/hsiang-han/unraid_templates`
2. Find "CosyVoice3-API" in Community Applications
3. Configure device and FP16 settings
4. Start — first launch downloads model, subsequent starts are fast

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/audio/speech` | POST | Text-to-speech (OpenAI-compatible) |
| `/v1/audio/speech/clone` | POST | Zero-shot voice cloning |
| `/v1/voices` | GET | List available voices |
| `/v1/models` | GET | List models |
| `/health` | GET | Health check |
| `/docs` | GET | Swagger documentation |

## License

Apache-2.0 (same as upstream CosyVoice)
