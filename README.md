# Task API

A simple to-do list CRUD API built with FastAPI (Python).
Tasks are stored in memory, so they reset when you restart the server.

## How to run

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Then open http://localhost:8000/docs for Swagger UI.

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | / | API info |
| GET | /health | Health check |
| GET | /tasks | List all tasks |
| GET | /tasks/{id} | Get one task |
| POST | /tasks | Create a task |
| PUT | /tasks/{id} | Update a task |
| DELETE | /tasks/{id} | Delete a task |

## Example curl

```bash
curl -i http://localhost:8000/tasks/1
```

```text
HTTP/1.1 200 OK
content-type: application/json

{"id":1,"title":"Learn FastAPI","done":false}
```

## Swagger screenshot

![Swagger UI](docs/swagger.png)
