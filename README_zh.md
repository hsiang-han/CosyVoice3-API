# CosyVoice3-API

[English](README.md)

基于 [CosyVoice 3](https://github.com/FunAudioLLM/CosyVoice)（阿里 FunAudioLLM）的 OpenAI 兼容语音合成 API。

3 秒参考音频即可克隆声音，注册一次永久使用。支持 RTX 50 系列（Blackwell）显卡。

## 功能特性

- OpenAI 兼容的 `/v1/audio/speech` 接口（JSON body）
- 3 秒零样本声音克隆
- 音色注册——克隆一次，之后按名称使用
- 流式输出支持（`"stream": true` 返回原始 PCM）
- 9 种语言，18 种中文方言
- 支持 RTX 50 系列（Blackwell）及更早的 GPU

## 快速开始

```bash
docker run -d --gpus all --shm-size=2g \
  -p 8080:8080 \
  -v /mnt/user/appdata/cosyvoice3-api/models:/root/.cache/models \
  -e HF_ENDPOINT=https://huggingface.co \
  --name cosyvoice3-api \
  ghcr.io/hsiang-han/cosyvoice3-api:latest
```

首次启动从 HuggingFace 下载模型（约 10GB）。国内用户设置 `HF_ENDPOINT=https://hf-mirror.com` 加速下载。

## 使用方法

### 第一步：注册音色（首次使用必须）

CosyVoice3 没有内置音色，需要先用参考音频注册：

```bash
curl -X POST http://localhost:8080/v1/voices/register \
  -F "voice_id=my_voice" \
  -F "prompt_text=这是参考音频中说的话的文字内容" \
  -F "prompt_wav=@reference.wav"
```

注册的音色在容器重启后仍然可用。

### 第二步：生成语音

```bash
curl -X POST http://localhost:8080/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"input": "你好，世界", "voice": "my_voice"}' \
  --output speech.wav
```

### 流式输出

```bash
curl -X POST http://localhost:8080/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"input": "你好，世界", "voice": "my_voice", "stream": true}' \
  --output speech.pcm
```

返回原始 PCM（16-bit，单声道，24000Hz）。响应头包含 `X-Sample-Rate`、`X-Channels`、`X-Bit-Depth`。

### 一次性声音克隆（不注册）

```bash
curl -X POST http://localhost:8080/v1/audio/speech/clone \
  -F "input=这是克隆的声音" \
  -F "prompt_text=这是参考音频中说的话" \
  -F "prompt_wav=@reference.wav" \
  --output cloned.wav
```

### 查看/删除音色

```bash
curl http://localhost:8080/v1/voices

curl -X DELETE http://localhost:8080/v1/voices/my_voice
```

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/v1/audio/speech` | POST | 语音合成（JSON body，OpenAI 兼容） |
| `/v1/audio/speech/clone` | POST | 一次性声音克隆（Form + 文件上传） |
| `/v1/voices/register` | POST | 注册音色 |
| `/v1/voices/{voice_id}` | DELETE | 删除已注册音色 |
| `/v1/voices` | GET | 列出已注册音色 |
| `/v1/models` | GET | 列出模型 |
| `/health` | GET | 健康检查 |
| `/docs` | GET | Swagger 文档 |

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| MODEL_DIR | FunAudioLLM/Fun-CosyVoice3-0.5B-2512 | HuggingFace 模型 ID 或本地路径 |
| HF_ENDPOINT | https://huggingface.co | HuggingFace 镜像地址（国内用 https://hf-mirror.com） |
| FP16 | true | 半精度推理，减少约 50% 显存 |

## 硬件要求

- NVIDIA 显卡，4GB+ 显存（FP16）或 8GB+（FP32）
- 驱动版本 550+（Ampere/Ada）或 570+（Blackwell RTX 50 系列）
- 安装 NVIDIA Container Toolkit 的 Docker 环境

## 致谢

- [CosyVoice](https://github.com/FunAudioLLM/CosyVoice) — 阿里 FunAudioLLM 团队，模型和推理框架

## 许可证

Apache-2.0（与上游 CosyVoice 一致）
