
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Dict, Any, List
import io

from .config import settings
from .models import Snapshot, CommentaryResponse, Segment
from .state import store
from .utils import compute_news, mark_cooldown, within_cooldown, register_phrases
from .generator import generate_segments
from .tts import synthesize_segments

app = FastAPI(title="Commentary ElevenLabs FastAPI", version="1.0.0")

@app.get("/health")
def health():
    return {"ok": True, "openai": bool(settings.OPENAI_API_KEY), "eleven": bool(settings.ELEVEN_API_KEY)}

@app.post("/commentary", response_class=StreamingResponse)
async def commentary(snapshot: Snapshot):
    # 1) Load state per (match_id, customer_id)
    mid = snapshot.snapshot_meta.match_id
    cid = snapshot.customer.id
    state = store.get(mid, cid)

    # 2) Compute what's new
    news = compute_news(snapshot, state)

    # 3) If nothing new and no score change → remain silent
    has_news = any(len(v) for v in news.values())
    score_changed = (snapshot.match_info.score.home != state.last_score.home) or (snapshot.match_info.score.away != state.last_score.away)
    if not has_news and not score_changed:
        return StreamingResponse(iter([b""]), media_type="application/octet-stream", headers={"X-Commentary": "no-news"})

    # 4) Cooldowns per type (simple gate)
    # Gate some categories if too frequent
    gated_news = { "goals": [], "events": [], "bets": [], "promos": [] }
    if news["goals"] and not within_cooldown(state, "Goal"):
        gated_news["goals"] = news["goals"]
        mark_cooldown(state, "Goal")
    if news["events"]:
        # We'll not cooldown general events by default; could add per-type later
        gated_news["events"] = news["events"]
    if news["bets"] and not within_cooldown(state, "Bet"):
        gated_news["bets"] = news["bets"]
        mark_cooldown(state, "Bet")
    if news["promos"] and not within_cooldown(state, "Promo"):
        gated_news["promos"] = news["promos"]
        mark_cooldown(state, "Promo")

    # If all gated out, remain silent
    if not any(len(v) for v in gated_news.values()) and not score_changed:
        return StreamingResponse(iter([b""]), media_type="application/octet-stream", headers={"X-Commentary": "gated"})

    # 5) Generate text segments (OpenAI or fallback)
    segments: List[Segment] = generate_segments(snapshot, state, gated_news)
    if not segments and not score_changed:
        return StreamingResponse(iter([b""]), media_type="application/octet-stream", headers={"X-Commentary": "no-segments"})

    # 6) Synthesize with ElevenLabs
    voices = {
        "pbp": snapshot.customer.tts_prefs.voice_id_main,
        "analyst": snapshot.customer.tts_prefs.voice_id_analyst
    }
    wav_bytes = await synthesize_segments(segments, voices)

    # 7) Update state after successful audio creation
    for g in gated_news["goals"]:
        state.processed_event_ids.add(g.event_id)
    for ev in gated_news["events"]:
        state.processed_event_ids.add(ev.event_id)
    state.last_score = snapshot.match_info.score
    register_phrases(state, [s.text for s in segments])

    # Stream WAV
    return StreamingResponse(io.BytesIO(wav_bytes), media_type="audio/wav",
                             headers={"X-Commentary": "ok", "X-Segments": str(len(segments))})
