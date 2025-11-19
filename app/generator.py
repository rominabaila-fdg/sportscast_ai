
from __future__ import annotations
from typing import List, Dict, Any, Optional
import os

from openai import OpenAI
from .models import Snapshot, Segment, Goal, GenericEvent
from .prompts import build_messages, PBP_STYLE, ANALYST_STYLE, PERSONAL_STYLE
from .utils import map_player_name, team_name, score_str, coalesce_goals, is_repetitive
from .config import settings

# OpenAI client (new SDK)
_client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None

def _fallback_simple_line(txt: str) -> str:
    # fallback if OpenAI is unavailable
    return txt

def _ask_openai(context: str, style: str) -> str:
    if not _client:
        return _fallback_simple_line(context)
    try:
        resp = _client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=build_messages(context, style),
            temperature=0.75,
            max_tokens=140,
            n=1,
        )
        content = resp.choices[0].message.content.strip()
        return content
    except Exception as e:
        return _fallback_simple_line(context)

def generate_segments(snapshot: Snapshot, state, news: Dict[str, List]) -> List[Segment]:
    segments: List[Segment] = []
    minute_now = snapshot.match_info.clock.minute
    # Pron dict (optional fallback)
    pron = {p.grapheme: p.alias for p in snapshot.pronunciation_dictionary}

    # 1) Goals (coalesced groups)
    goal_groups = coalesce_goals(news.get("goals", []))
    for group in goal_groups:
        if not group:
            continue
        # build concise context string
        lines = []
        for g in group:
            scorer = map_player_name(snapshot, g.scorer_id)
            team = team_name(snapshot, g.team_id)
            lines.append(f"{g.clock.minute}’: {team} — {scorer} ({g.description_short or ''}) → {score_str(g.score_after)}")
        context = " | ".join(lines)
        prompt = f"Context: {snapshot.match_info.rivalry or ''}, {snapshot.match_info.arena or ''}. Noutăți: {context}. Scrie 1–2 fraze."
        text = _ask_openai(prompt, PBP_STYLE)
        if not is_repetitive(state, text):
            segments.append(Segment(role="pbp", text=text, minute=minute_now))

    # 2) Other events (ordered by minute ascending)
    others = sorted(news.get("events", []), key=lambda e: e.clock.elapsed_seconds)
    if others:
        bullets = []
        for ev in others:
            minute = ev.clock.minute
            tname = team_name(snapshot, ev.team_id) if ev.team_id else ""
            # players (if any)
            names = []
            for pid in ev.player_ids or []:
                names.append(map_player_name(snapshot, pid))
            names_str = ", ".join(names) if names else ""
            b = f"{minute}’: {ev.type} {tname} {names_str} — {ev.detail_short or ''}".strip()
            bullets.append(b)
        context = " | ".join(bullets)
        prompt = f"Context: {snapshot.match_info.rivalry or ''}, {snapshot.match_info.arena or ''}. Noutăți: {context}. Scrie 1 frază informativă."
        text = _ask_openai(prompt, ANALYST_STYLE)
        if text and not is_repetitive(state, text):
            segments.append(Segment(role="analyst", text=text, minute=minute_now))

    # 3) Bets & promos (personalized)
    # Bets
    bet_line: Optional[str] = None
    for b in news.get("bets", []):
        # build minimal change line
        sel_bits = []
        for sel in b.selections:
            bit = f"{sel.market}:{sel.state}"
            if sel.result:
                bit += f"({sel.result})"
            sel_bits.append(bit)
        bet_line = f"{snapshot.customer.name}, " + "; ".join(sel_bits)
        break

    # Promo (take first)
    promo_line: Optional[str] = None
    promos = news.get("promos", [])
    if promos:
        pr = promos[0]
        trig = pr.trigger.type.replace("_", " ")
        promo_line = f"Notă: {pr.source} — {trig} — {pr.reward}."

    if bet_line or promo_line:
        txt = " ".join([x for x in [bet_line, promo_line] if x])
        text = _ask_openai(f"Context personalizat: {txt}. Scrie 1 frază, neutră.", PERSONAL_STYLE)
        if text and not is_repetitive(state, text):
            segments.append(Segment(role="personalized", text=text, minute=minute_now))

    return segments
