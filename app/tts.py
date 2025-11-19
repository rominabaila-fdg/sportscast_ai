
from __future__ import annotations
import io, wave, asyncio
from typing import List, Dict, Any, Optional
import httpx

from .config import settings
from .models import Segment

# Assemble PCM_16000 into a single WAV and return bytes
def pcm16_to_wav_bytes(pcm: bytes, samplerate: int = 16000, channels: int = 1) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(2)  # 16-bit
        w.setframerate(samplerate)
        w.writeframes(pcm)
    return buf.getvalue()

async def tts_segment(client: httpx.AsyncClient, text: str, voice_id: str,
                      previous_text: str = "", next_text: str = "") -> bytes:
    url = f"{settings.ELEVEN_BASE_URL}/v1/text-to-speech/{voice_id}/stream"
    params = {
        "optimize_streaming_latency": settings.ELEVEN_OPTIMIZE_LATENCY,
        "output_format": settings.ELEVEN_OUTPUT_FORMAT,  # pcm_16000
    }
    body = {
        "text": text,
        "model_id": settings.ELEVEN_MODEL_ID,
        "voice_settings": {
            "stability": 0.55,
            "similarity_boost": 0.85,
            "style": 0.25,
            "use_speaker_boost": True
        }
    }
    # Provide continuity hints if supported (ignored otherwise)
    if previous_text:
        body["previous_text"] = previous_text
    if next_text:
        body["next_text"] = next_text

    headers = {
        "xi-api-key": settings.ELEVEN_API_KEY,
        "Accept": "application/octet-stream"
    }

    pcm = bytearray()
    async with client.stream("POST", url, params=params, json=body, headers=headers, timeout=60) as r:
        r.raise_for_status()
        async for chunk in r.aiter_bytes():
            if chunk:
                pcm.extend(chunk)
    return bytes(pcm)

async def synthesize_segments(segments: List[Segment], voices: Dict[str, str]) -> bytes:
    # Decide voice per role
    async with httpx.AsyncClient() as client:
        combined_pcm = bytearray()
        for i, seg in enumerate(segments):
            voice_id = voices["pbp"] if seg.role == "pbp" else (voices["analyst"] if seg.role == "analyst" else voices["pbp"])
            prev_text = segments[i-1].text if i > 0 else ""
            next_text = segments[i+1].text if i+1 < len(segments) else ""
            pcm = await tts_segment(client, seg.text, voice_id, previous_text=prev_text, next_text=next_text)
            combined_pcm.extend(pcm)
    wav_bytes = pcm16_to_wav_bytes(bytes(combined_pcm), samplerate=16000, channels=1)
    return wav_bytes
