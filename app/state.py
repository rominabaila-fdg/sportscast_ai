
from __future__ import annotations
from typing import Dict, Set, Deque, Tuple, Optional
from collections import deque
from dataclasses import dataclass, field
from time import time

from .models import Score

@dataclass
class MatchState:
    last_score: Score = field(default_factory=lambda: Score(home=0, away=0))
    last_period: str = "1H"
    last_minute: int = 0
    processed_event_ids: Set[str] = field(default_factory=set)
    last_betslip_state_hash: Optional[str] = None
    last_promo_state_hash: Optional[str] = None
    recent_phrases: Deque[str] = field(default_factory=lambda: deque(maxlen=20))
    last_event_time_by_type: Dict[str, float] = field(default_factory=dict)  # epoch seconds
    updated_at: float = field(default_factory=time)

class InMemoryStore:
    def __init__(self):
        self._store: Dict[Tuple[str, str], MatchState] = {}

    def get(self, match_id: str, customer_id: str) -> MatchState:
        key = (match_id, customer_id)
        if key not in self._store:
            self._store[key] = MatchState()
        return self._store[key]

    def set(self, match_id: str, customer_id: str, state: MatchState):
        self._store[(match_id, customer_id)] = state

    def clear(self, match_id: str, customer_id: str):
        self._store.pop((match_id, customer_id), None)

store = InMemoryStore()
