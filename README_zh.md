# CosyVoice3-API

[English](README.md) | [中文](README_zh.md)

OpenAI 兼容的文本转语音 API，基于 [CosyVoice 3](https://github.com/FunAudioLLM/CosyVoice)（阿里通义 FunAudioLLM）。

无多余组件、仅通过 FastAPI 提供模型推理和 OpenAI 兼容接口。支持预设音色、指令控制和零样本语音克隆。

## 相比官方的改进

官方 CosyVoice 仓库需要手动配置，无法在 Unraid 等平台中直接使用。本项目添加了 entrypoint 使其开箱即用，同时兼容任何 Docker 环境：
- 容器启动自动运行 API 服务
- OpenAI 兼容 `/v1/audio/speech` 接口
- 零样本语音克隆接口 `/v1/audio/speech/clone`
- 通过环境变量控制 GPU 和显存
- Unraid Community Applications 模板

## 快速开始

```bash
docker run -d --gpus all --shm-size=2g \
  -p 8080:8080 \
  -v /path/to/models:/root/.cache/modelscope/hub \
  ghcr.io/hsiang-han/cosyvoice3-api:latest
```

首次启动会下载模型（约 2GB）。

## 使用方法

### 文本转语音（OpenAI 兼容）

```bash
curl -X POST http://localhost:8080/v1/audio/speech \
  -F "input=你好，世界" \
  -F "voice=中文女" \
  --output speech.wav
```

### 指令控制

```bash
curl -X POST http://localhost:8080/v1/audio/speech \
  -F "input=今天天气真好" \
  -F "voice=中文女" \
  -F "instruct_text=用开心的语气说" \
  --output happy.wav
```

### 语音克隆

```bash
curl -X POST http://localhost:8080/v1/audio/speech/clone \
  -F "input=这是克隆的声音" \
  -F "prompt_text=这是参考音频中说的话" \
  -F "prompt_wav=@reference.wav" \
  --output cloned.wav
```

### 查看可用音色

```bash
curl http://localhost:8080/v1/voices
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MODEL_DIR` | `FunAudioLLM/Fun-CosyVoice3-0.5B-2512` | ModelScope 模型 ID |
| `FP16` | `true` | 半精度推理，显存减少约 50% |
| `PORT` | `8080` | API 服务端口 |

## 显存占用

| 配置 | 预估显存 |
|------|---------|
| FP16=true（默认） | ~3-4GB |
| FP16=false | ~6-8GB |

## Unraid 安装

1. 添加模板仓库：`https://github.com/hsiang-han/unraid_templates`
2. 在 Community Applications 中搜索 "CosyVoice3-API"
3. 配置设备和 FP16 设置
4. 启动——首次启动下载模型，之后秒启动

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/v1/audio/speech` | POST | 文本转语音（OpenAI 兼容） |
| `/v1/audio/speech/clone` | POST | 零样本语音克隆 |
| `/v1/voices` | GET | 列出可用音色 |
| `/v1/models` | GET | 列出模型 |
| `/health` | GET | 健康检查 |
| `/docs` | GET | Swagger 文档 |

## 许可证

Apache-2.0（与上游 CosyVoice 一致）
