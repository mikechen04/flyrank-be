# Task API

A small in-memory to-do list **CRUD API** built with **Python** and **FastAPI**.

You can create, read, update, and delete tasks. Data lives only in memory — restarting the server resets it. Interactive docs are available via Swagger UI.

## Install & run

```bash
python -m venv .venv
```

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**macOS / Linux:**

```bash
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Then open:

- API: http://localhost:8000/
- Swagger UI: http://localhost:8000/docs

## Endpoints

| Method | Path | Status codes | Description |
|--------|------|--------------|-------------|
| GET | `/` | 200 | API name, version, endpoints |
| GET | `/health` | 200 | Health check |
| GET | `/tasks` | 200 | List all tasks |
| GET | `/tasks/{id}` | 200, 404 | Get one task |
| POST | `/tasks` | 201, 400 | Create a task (`{"title": "..."}`) |
| PUT | `/tasks/{id}` | 200, 400, 404 | Update `title` and/or `done` |
| DELETE | `/tasks/{id}` | 204, 404 | Delete a task |

## Example: `curl -i`

```text
HTTP/1.1 200 OK
date: Wed, 22 Jul 2026 10:02:15 GMT
server: uvicorn
content-length: 45
content-type: application/json

{"id":1,"title":"Learn FastAPI","done":false}
```

Command used:

```bash
curl -i http://localhost:8000/tasks/1
```

Create a task:

```bash
curl -i -X POST http://localhost:8000/tasks ^
  -H "Content-Type: application/json" ^
  -d "{\"title\":\"Buy milk\"}"
```

(On macOS/Linux, use `\` for line breaks and single quotes around the JSON body.)

## Swagger UI

Open http://localhost:8000/docs and use **Try it out** to run the full CRUD cycle without curl.

![Swagger UI screenshot](docs/swagger.png)

> Add your screenshot: with the server running, open `/docs`, take a screenshot, and save it as `docs/swagger.png`.

## Project structure

```text
flyrank-be/
├── main.py              # API (in-memory tasks)
├── requirements.txt     # fastapi, uvicorn
├── README.md
└── docs/
    └── swagger.png      # Swagger UI screenshot
```

## Notes

- Storage is an in-memory list — no database and no files.
- Missing or empty `title` on POST/PUT → `400` with a JSON error.
- Unknown task id → `404` with `{"error": "Task N not found"}`.
- Successful DELETE → `204` with an empty body.
