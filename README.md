# Commentary ElevenLabs FastAPI

End-to-end FastAPI service that receives JSON data, generates text commentary (OpenAI)
and returns audio (ElevenLabs TTS streaming, PCM_16000 → WAV). Includes state management,
change detection, anti-repetition rules, event prioritization and content personalization.

## Requirements
- Python 3.10+
- OpenAI account (OPENAI_API_KEY)
- ElevenLabs account (ELEVENLABS_API_KEY)

## Installation
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration (env)
```bash
export OPENAI_API_KEY=sk-...
export ELEVENLABS_API_KEY=...
export OPENAI_MODEL=gpt-4o-mini
# optional:
export ELEVEN_MODEL_ID=eleven_flash_v2_5
export ELEVEN_OUTPUT_FORMAT=pcm_16000
export ELEVEN_OPTIMIZE_LATENCY=0
```

## Running
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Endpoints
- `POST /commentary` – Body: JSON data. Response: `audio/wav` (stream).
- `GET /health` – API keys status.
