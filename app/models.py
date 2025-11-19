
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# ------------ Snapshot schema (clean) ------------

class Clock(BaseModel):
    elapsed_seconds: int
    minute: int
    seconds_in_period: int
    stoppage_seconds: int

class Score(BaseModel):
    home: int
    away: int

class Player(BaseModel):
    id: int
    player_name: str
    tshirt_number: int
    position: str
    age: Optional[int] = None
    joined_team: Optional[str] = None
    pron_alias: Optional[str] = None

class Team(BaseModel):
    team_id: str
    name: str
    is_home_team: bool
    players_roster: List[Player]

class MatchInfo(BaseModel):
    period: str
    clock: Clock
    score: Score
    arena: Optional[str] = None
    city: Optional[str] = None
    rivalry: Optional[str] = None
    teams: List[Team]

class Goal(BaseModel):
    event_id: str
    period: str
    clock: Clock
    team_id: str
    scorer_id: int
    assist_id: Optional[int] = None
    body_part: Optional[str] = None
    situation: Optional[str] = None
    description_short: Optional[str] = None
    score_after: Score

class GenericEvent(BaseModel):
    event_id: str
    type: str
    period: str
    clock: Clock
    team_id: Optional[str] = None
    player_ids: List[int] = []
    detail_short: Optional[str] = None
    tags: List[str] = []
    source: Optional[str] = None
    confidence: Optional[float] = None
    score_after: Optional[Score] = None

class TtsPrefs(BaseModel):
    voice_id_main: str
    voice_id_analyst: str
    energy_bias: Optional[str] = "medium_high"
    profanity_filter: Optional[bool] = True

class Customer(BaseModel):
    id: str
    name: str
    locale: Optional[str] = "ro-RO"
    tts_prefs: TtsPrefs

class Selection(BaseModel):
    selection_id: str
    market: str
    description: Optional[str] = ""
    state: str
    result: Optional[str] = ""
    is_active: bool
    settled: bool

class Odds(BaseModel):
    original_decimal: float
    live_decimal: float

class PayoutInfo(BaseModel):
    stake: float
    potential_payout: float
    current_partial_payout: float
    currency: str
    odds: Odds
    cashout_available: Optional[bool] = False
    cashout_value: Optional[float] = 0.0

class Betslip(BaseModel):
    betslip_id: str
    belongs_to_customer_id: str
    event_id: str
    selections: List[Selection]
    payout_info: PayoutInfo
    timestamps: Dict[str, str]

class Trigger(BaseModel):
    type: str
    window_seconds: Optional[int] = None

class Promotion(BaseModel):
    promotion_id: str
    source: str
    trigger: Trigger
    reward: str
    expires_at: Optional[str] = None

class PronEntry(BaseModel):
    grapheme: str
    alias: str

class MatchStatistics(BaseModel):
    goals: List[Goal] = []

class SnapshotMeta(BaseModel):
    snapshot_id: str
    sequence_no: int
    generated_at: str
    match_id: str

class Snapshot(BaseModel):
    snapshot_meta: SnapshotMeta
    match_info: MatchInfo
    match_statistics: MatchStatistics
    events: List[GenericEvent] = []
    customer: Customer
    betslips: List[Betslip] = []
    promotions: List[Promotion] = []
    pronunciation_dictionary: List[PronEntry] = []

# ------------ Output models ------------

class Segment(BaseModel):
    role: str  # 'pbp' | 'analyst' | 'personalized'
    text: str
    minute: int
    previous_text: str = ""
    next_text: str = ""

class CommentaryResponse(BaseModel):
    audio_mime: str = "audio/wav"
    duration_sec: Optional[float] = None
    segments: List[Segment]
    used_voice_ids: List[str]
