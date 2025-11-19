
# Commentary ElevenLabs FastAPI

End-to-end FastAPI service care primește snapshotul JSON „curat”, generează text (OpenAI)
și returnează audio (ElevenLabs TTS streaming, PCM_16000 → WAV). Include stare, diff,
reguli anti-repetiție, prioritizare/coalescing, personalizare betslip și promo.

## Cerințe
- Python 3.10+
- Cont OpenAI (OPENAI_API_KEY)
- Cont ElevenLabs (ELEVENLABS_API_KEY)

## Instalare
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Config (env)
```bash
export OPENAI_API_KEY=sk-...
export ELEVENLABS_API_KEY=...
export OPENAI_MODEL=gpt-4o-mini
# opțional:
export ELEVEN_MODEL_ID=eleven_flash_v2_5
export ELEVEN_OUTPUT_FORMAT=pcm_16000
export ELEVEN_OPTIMIZE_LATENCY=0
```

## Rulare
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Endpoint
- `POST /commentary` – Body: snapshot JSON „curat”. Răspuns: `audio/wav` (stream).
- `GET /health` – stare API keys.

## Note
- Serviciul e **stateful** per `(match_id, customer.id)` (in-memory). Pentru producție, folosește Redis.
- Pronunții: încarcă dicționarele în ElevenLabs (preferat). Codul folosește doar text curat;
  dacă e nevoie, poți insera aliasuri în text înainte de TTS.
- Audio: folosim `pcm_16000` din ElevenLabs, concatenăm segmentele și livrăm WAV.
- Anti-repetiție: ring buffer fraze + cooldown pe tipuri (config în env).

## Extensii ușoare
- Redis store, logs centralizate, test de latență, fallback TTS local dacă ElevenLabs nu răspunde.
- Reguli extra pe `events` (Penalty, VAR confirmat etc.) și scoring contextual.
