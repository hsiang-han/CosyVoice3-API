import io
import os
import tempfile
import wave
from contextlib import asynccontextmanager
from typing import Optional

import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel

MODEL_DIR = os.getenv("MODEL_DIR", "FunAudioLLM/Fun-CosyVoice3-0.5B-2512")
FP16 = os.getenv("FP16", "true").lower() == "true"
SAMPLE_RATE = 24000

_model = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _model
    from cosyvoice.cli.cosyvoice import AutoModel

    _model = AutoModel(
        model_dir=MODEL_DIR,
        fp16=FP16,
    )
    yield
    _model = None


app = FastAPI(title="CosyVoice3-API", version="0.1.0", lifespan=lifespan)


@app.get("/health")
async def health():
    return {
        "status": "ok" if _model else "loading",
        "model": MODEL_DIR,
        "fp16": FP16,
    }


@app.get("/v1/models")
async def list_models():
    voices = _get_voices()
    return {
        "object": "list",
        "data": [
            {
                "id": "cosyvoice3",
                "object": "model",
                "owned_by": "FunAudioLLM",
                "available_voices": voices,
            }
        ],
    }


@app.get("/v1/voices")
async def list_voices():
    return {"voices": _get_voices()}


class SpeechRequest(BaseModel):
    model: Optional[str] = "cosyvoice3"
    input: str
    voice: Optional[str] = None
    response_format: str = "wav"
    speed: float = 1.0
    stream: bool = False


@app.post("/v1/audio/speech")
async def text_to_speech(req: SpeechRequest):
    if not _model:
        raise HTTPException(status_code=503, detail="Model not loaded")

    if not req.input.strip():
        raise HTTPException(status_code=400, detail="Input text is empty")

    voices = _get_voices()
    if not req.voice and not voices:
        raise HTTPException(
            status_code=400,
            detail="No voice specified and no registered voices available. Register a voice first via POST /v1/voices/register",
        )

    voice = req.voice or voices[0]
    if voice not in _get_voices():
        raise HTTPException(status_code=400, detail=f"Voice '{voice}' not found. Available: {_get_voices()}")

    if req.stream:
        return StreamingResponse(
            _stream_synthesis(req.input, voice, req.speed),
            media_type="audio/pcm",
            headers={"X-Sample-Rate": str(SAMPLE_RATE), "X-Channels": "1", "X-Bit-Depth": "16"},
        )

    audio_data = _synthesize(req.input, voice, req.speed)
    wav_bytes = _to_wav(audio_data)
    return Response(content=wav_bytes, media_type="audio/wav")


@app.post("/v1/audio/speech/clone")
async def clone_speech(
    input: str = Form(...),
    prompt_text: str = Form(...),
    prompt_wav: UploadFile = File(...),
    speed: float = Form(default=1.0),
):
    if not _model:
        raise HTTPException(status_code=503, detail="Model not loaded")

    if not input.strip():
        raise HTTPException(status_code=400, detail="Input text is empty")

    prompt_bytes = await prompt_wav.read()

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(prompt_bytes)
        tmp_path = tmp.name

    try:
        audio_data = _clone(input, prompt_text, tmp_path, speed)
    finally:
        os.unlink(tmp_path)

    wav_bytes = _to_wav(audio_data)
    return Response(content=wav_bytes, media_type="audio/wav")


@app.post("/v1/voices/register")
async def register_voice(
    voice_id: str = Form(...),
    prompt_text: str = Form(...),
    prompt_wav: UploadFile = File(...),
):
    """Register a voice from reference audio. Once registered, use it by name in /v1/audio/speech."""
    if not _model:
        raise HTTPException(status_code=503, detail="Model not loaded")

    if not voice_id.strip():
        raise HTTPException(status_code=400, detail="voice_id is empty")

    if not prompt_text.strip():
        raise HTTPException(status_code=400, detail="prompt_text is empty")

    existing = _get_voices()
    if voice_id in existing:
        raise HTTPException(status_code=409, detail=f"Voice '{voice_id}' already exists. Delete it first or use a different name.")

    prompt_bytes = await prompt_wav.read()

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(prompt_bytes)
        tmp_path = tmp.name

    try:
        _model.add_zero_shot_spk(prompt_text, tmp_path, voice_id)
        _model.save_spkinfo()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register voice: {e}")
    finally:
        os.unlink(tmp_path)

    return {"status": "ok", "voice_id": voice_id, "total_voices": len(_get_voices())}


@app.delete("/v1/voices/{voice_id}")
async def delete_voice(voice_id: str):
    """Delete a registered voice."""
    if not _model:
        raise HTTPException(status_code=503, detail="Model not loaded")

    if voice_id not in _get_voices():
        raise HTTPException(status_code=404, detail=f"Voice '{voice_id}' not found")

    del _model.frontend.spk2info[voice_id]
    _model.save_spkinfo()

    return {"status": "ok", "deleted": voice_id, "remaining_voices": len(_get_voices())}


def _get_voices() -> list:
    if not _model or not hasattr(_model, "list_available_spks"):
        return []
    return _model.list_available_spks()


def _synthesize(text: str, voice: str, speed: float) -> np.ndarray:
    all_audio = []
    for output in _model.inference_sft(text, voice, stream=False, speed=speed):
        all_audio.append(output["tts_speech"].numpy().flatten())
    return np.concatenate(all_audio)


def _stream_synthesis(text: str, voice: str, speed: float):
    for output in _model.inference_sft(text, voice, stream=True, speed=speed):
        chunk = output["tts_speech"].numpy().flatten()
        chunk_clipped = np.clip(chunk, -1.0, 1.0)
        yield (chunk_clipped * 32767).astype(np.int16).tobytes()


def _clone(text: str, prompt_text: str, prompt_wav_path: str, speed: float) -> np.ndarray:
    all_audio = []
    for output in _model.inference_zero_shot(text, prompt_text, prompt_wav_path, stream=False, speed=speed):
        all_audio.append(output["tts_speech"].numpy().flatten())
    return np.concatenate(all_audio)


def _to_wav(audio: np.ndarray) -> bytes:
    audio_clipped = np.clip(audio, -1.0, 1.0)
    audio_int16 = (audio_clipped * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_int16.tobytes())
    return buf.getvalue()
