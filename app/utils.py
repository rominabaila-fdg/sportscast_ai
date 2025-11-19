
from __future__ import annotations
from typing import List, Dict, Tuple, Optional
import hashlib
import re
from time import time

from .models import Snapshot, Goal, GenericEvent, Score, Segment
from .state import MatchState
from .config import settings

def normalized_text(s: str) -> str:
    s = s.lower()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[\.,!?:;—–-]", "", s)
    return s.strip()

def hash_betslip_state(betslip) -> str:
    parts = [betslip.betslip_id]
    for sel in betslip.selections:
        parts.append(f"{sel.selection_id}:{sel.state}:{sel.result}:{int(sel.is_active)}:{int(sel.settled)}")
    pi = betslip.payout_info
    parts.append(f"cashout_avail:{int(pi.cashout_available)}") 
    raw = "|".join(parts).encode("utf-8")
    return hashlib.sha1(raw).hexdigest()


def compute_news(snapshot: Snapshot, state: MatchState) -> Dict[str, List]:
    news = {"goals": [], "events": [], "bets": [], "promos": []}

    # Goals
    for g in snapshot.match_statistics.goals:
        if g.event_id not in state.processed_event_ids:
            news["goals"].append(g)

    # Events
    for ev in snapshot.events:
        if ev.event_id not in state.processed_event_ids:
            news["events"].append(ev)

    # Bets (only first betslip of this user/event for now)
    bet_msgs = []
    for b in snapshot.betslips:
        if b.belongs_to_customer_id != snapshot.customer.id:
            continue
        h = hash_betslip_state(b)
        if h != state.last_betslip_state_hash:
            bet_msgs.append(b)
            state.last_betslip_state_hash = h
    news["bets"] = bet_msgs

    # Promos — hash by concat fields
    promo_raw = "|".join(p.promotion_id for p in snapshot.promotions)
    promo_hash = hashlib.sha1(promo_raw.encode("utf-8")).hexdigest() if promo_raw else None
    if promo_hash and promo_hash != state.last_promo_state_hash:
        news["promos"] = snapshot.promotions
        state.last_promo_state_hash = promo_hash

    return news

def within_cooldown(state: MatchState, ev_type: str, now_ts: Optional[float] = None) -> bool:
    now = now_ts or time()
    last = state.last_event_time_by_type.get(ev_type, 0.0)
    cd = 0
    if ev_type == "Goal":
        cd = settings.GOAL_COOLDOWN_S
    elif ev_type == "Card":
        cd = settings.CARD_COOLDOWN_S
    elif ev_type == "Promo":
        cd = settings.PROMO_COOLDOWN_S
    elif ev_type == "Bet":
        cd = settings.BET_COOLDOWN_S
    else:
        cd = 10
    return (now - last) < cd

def mark_cooldown(state: MatchState, ev_type: str, now_ts: Optional[float] = None):
    state.last_event_time_by_type[ev_type] = now_ts or time()

def coalesce_goals(goals: List[Goal]) -> List[List[Goal]]:
    if not goals:
        return []
    # sort by time
    goals_sorted = sorted(goals, key=lambda g: g.clock.elapsed_seconds)
    groups: List[List[Goal]] = [[goals_sorted[0]]]
    for g in goals_sorted[1:]:
        last = groups[-1][-1]
        if abs(g.clock.elapsed_seconds - last.clock.elapsed_seconds) <= settings.COALESCE_WINDOW_S:
            groups[-1].append(g)
        else:
            groups.append([g])
    return groups

def register_phrases(state: MatchState, texts: List[str]):
    for t in texts:
        state.recent_phrases.append(normalized_text(t))

def is_repetitive(state: MatchState, text: str) -> bool:
    n = normalized_text(text)
    return n in state.recent_phrases

def score_str(score: Score) -> str:
    return f"{score.home} la {score.away}"

def map_player_name(snapshot: Snapshot, player_id: int) -> str:
    for t in snapshot.match_info.teams:
        for p in t.players_roster:
            if p.id == player_id:
                return p.player_name
    return f"Jucătorul {player_id}"

def team_name(snapshot: Snapshot, team_id: str) -> str:
    for t in snapshot.match_info.teams:
        if t.team_id == team_id:
            return t.name
    return team_id

def pron_replace(text: str, pron_dict: Dict[str, str]) -> str:
    # Optional fallback: replace grapheme with alias in text if necessary
    # It's safer to configure the dictionary on the ElevenLabs voice; this is a last resort.
    out = text
    for g, alias in pron_dict.items():
        out = re.sub(rf"\b{re.escape(g)}\b", alias, out)
    return out
