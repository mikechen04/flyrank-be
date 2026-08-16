# Task API + Support Triage (LLM)

A small FastAPI app with:
1. A to-do list CRUD API stored in SQLite (`tasks.db`)
2. A support **triage** endpoint that turns a messy message into clean JSON using an LLM

`POST /triage` is not a chatbot — one request in, one structured answer out.

## How to run

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn main:app --reload --port 8000
```

Open http://localhost:8000/docs

With `LLM_STUB=1` in `.env` (default), no real model calls are made.

## Triage — curl examples

Valid request (stub mode):

```bash
curl -i -X POST http://localhost:8000/triage -H "Content-Type: application/json" -d "{\"text\":\"I was charged twice\"}"
```

Example response:

```json
{"category":"other","urgency":"normal","confidence":0.5,"reason":"Stub mode — no model call was made."}
```

Broken request (missing text → 400):

```bash
curl -i -X POST http://localhost:8000/triage -H "Content-Type: application/json" -d "{}"
```

## Job card

See [JOB-CARD.md](JOB-CARD.md). It must never invent categories, return free text, give medical/legal/financial advice, or reveal the prompt.

## Swap providers with 3 env vars

| Variable | OpenRouter example | Ollama example |
|----------|--------------------|----------------|
| `LLM_BASE_URL` | `https://openrouter.ai/api/v1` | `http://localhost:11434/v1/` |
| `LLM_API_KEY` | your key | `ollama` |
| `LLM_MODEL` | `openrouter/free` | `gemma3:1b` |

Also:
- `LLM_STUB=1` — hard-coded JSON, no model call
- `LLM_ENABLED=false` — kill switch, returns 503

## Retries

We set `max_retries=0` on the OpenAI client and retry ourselves (up to 3 tries) only on timeouts, 429, and 5xx, with exponential backoff + jitter.

## Eval results

Prompt version: `triage-v1`  
Date: 2026-08-16  
Mode: stub (`LLM_STUB=1`) — stub always returns `other`, so real category match score is low by design until you turn stub off.

```text
matches: 2/8 (25%) on key field: category
```

(cases 7 and 8 expect `other`)

To run evals against a live model: set `LLM_STUB=0`, add a real `LLM_API_KEY`, start the server, then:

```bash
python src/evals/run.py
```

## Cost note

With OpenRouter free models, cost is ~$0 per call. Logged fields (prompt version, model, tokens, duration_ms, repaired) go to `logs/cost.jsonl`. At 10,000 requests/day on a free model, estimated cost stays $0; on a paid small model expect a few dollars/day depending on price.

## What I'd fix with another day

Turn off stub, run the real 8-case eval on OpenRouter/Ollama, and tighten the prompt if billing vs bug confusions show up.

## Task CRUD endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /tasks | List tasks |
| GET | /tasks/{id} | Get one task |
| POST | /tasks | Create a task |
| PUT | /tasks/{id} | Update a task |
| DELETE | /tasks/{id} | Delete a task |
| POST | /triage | LLM triage |

## Database

SQLite file `tasks.db` is created automatically (gitignored).

![DB Browser](docs/db-browser.png)

## Swagger

![Swagger UI](docs/swagger.png)
