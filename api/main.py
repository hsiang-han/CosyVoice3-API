import io
import os
import tempfile
import wave
from contextlib import asynccontextmanager
from typing import Optional

import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
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
    voices = []
    if _model and hasattr(_model, "list_available_spks"):
        voices = _model.list_available_spks()
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
    if not _model or not hasattr(_model, "list_available_spks"):
        return {"voices": []}
    return {"voices": _model.list_available_spks()}


class SpeechRequest(BaseModel):
    model: Optional[str] = "cosyvoice3"
    input: str
    voice: Optional[str] = None
    response_format: str = "wav"
    speed: float = 1.0
    instruct_text: Optional[str] = None


@app.post("/v1/audio/speech")
async def text_to_speech(req: SpeechRequest):
    if not _model:
        raise HTTPException(status_code=503, detail="Model not loaded")

    if not req.input.strip():
        raise HTTPException(status_code=400, detail="Input text is empty")

    audio_data = _synthesize(req.input, req.voice, req.instruct_text, req.speed)

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


def _synthesize(text: str, voice: Optional[str], instruct_text: Optional[str], speed: float) -> np.ndarray:
    all_audio = []

    if instruct_text and voice:
        for output in _model.inference_instruct(text, voice, instruct_text, stream=False, speed=speed):
            all_audio.append(output["tts_speech"].numpy().flatten())
    elif voice:
        for output in _model.inference_sft(text, voice, stream=False, speed=speed):
            all_audio.append(output["tts_speech"].numpy().flatten())
    else:
        spks = _model.list_available_spks() if hasattr(_model, "list_available_spks") else []
        default_voice = spks[0] if spks else None
        if default_voice:
            for output in _model.inference_sft(text, default_voice, stream=False, speed=speed):
                all_audio.append(output["tts_speech"].numpy().flatten())
        else:
            raise HTTPException(status_code=400, detail="No voice specified and no default voices available")

    return np.concatenate(all_audio)


def _clone(text: str, prompt_text: str, prompt_wav_path: str, speed: float) -> np.ndarray:
    all_audio = []
    for output in _model.inference_zero_shot(text, prompt_text, prompt_wav_path, stream=False, speed=speed):
        all_audio.append(output["tts_speech"].numpy().flatten())
    return np.concatenate(all_audio)


def _to_wav(audio: np.ndarray) -> bytes:
    audio_int16 = (audio * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_int16.tobytes())
    return buf.getvalue()
