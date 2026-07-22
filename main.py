import sqlite3

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

DB_PATH = "tasks.db"

app = FastAPI(title="Task API", version="1.0")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def row_to_task(row):
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}


def init_db():
    """Create tasks.db + table, and seed 3 tasks only if empty."""
    conn = get_conn()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    if count == 0:
        conn.executemany(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            [
                ("Learn FastAPI", 0),
                ("Build a CRUD API", 0),
                ("Push to GitHub", 1),
            ],
        )
        conn.commit()
    conn.close()


init_db()


def error(status: int, message: str):
    return JSONResponse(status_code=status, content={"error": message})


@app.get("/", summary="API info")
def root():
    """API name, version, and endpoints."""
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health", summary="Health check")
def health():
    """Check if the server is running."""
    return {"status": "ok"}


@app.get("/tasks", summary="List all tasks")
def list_tasks():
    """Return all tasks from the database."""
    conn = get_conn()
    rows = conn.execute("SELECT id, title, done FROM tasks").fetchall()
    conn.close()
    return [row_to_task(row) for row in rows]


@app.get("/tasks/{task_id}", summary="Get one task")
def get_task(task_id: int):
    """Get a task by id from the database."""
    conn = get_conn()
    row = conn.execute(
        "SELECT id, title, done FROM tasks WHERE id = ?", (task_id,)
    ).fetchone()
    conn.close()
    if not row:
        return error(404, "Task not found")
    return row_to_task(row)


@app.post("/tasks", status_code=201, summary="Create a task")
async def create_task(request: Request):
    """Create a new task in the database. Body needs a title."""
    try:
        body = await request.json()
    except Exception:
        return error(400, "body must be valid JSON")
    title = body.get("title") if isinstance(body, dict) else None
    if not title or not str(title).strip():
        return error(400, "title is required and must not be empty")

    conn = get_conn()
    cursor = conn.execute(
        "INSERT INTO tasks (title, done) VALUES (?, ?)",
        (str(title).strip(), 0),
    )
    conn.commit()
    task_id = cursor.lastrowid
    row = conn.execute(
        "SELECT id, title, done FROM tasks WHERE id = ?", (task_id,)
    ).fetchone()
    conn.close()
    return row_to_task(row)


@app.put("/tasks/{task_id}", summary="Update a task")
async def update_task(task_id: int, request: Request):
    """Update a task in the database (title and/or done)."""
    conn = get_conn()
    row = conn.execute(
        "SELECT id, title, done FROM tasks WHERE id = ?", (task_id,)
    ).fetchone()
    if not row:
        conn.close()
        return error(404, "Task not found")

    try:
        body = await request.json()
    except Exception:
        conn.close()
        return error(400, "body must be valid JSON")
    if not isinstance(body, dict) or ("title" not in body and "done" not in body):
        conn.close()
        return error(400, "body must include title and/or done")

    title = row["title"]
    done = row["done"]
    if "title" in body:
        if not body["title"] or not str(body["title"]).strip():
            conn.close()
            return error(400, "title must not be empty")
        title = str(body["title"]).strip()
    if "done" in body:
        if not isinstance(body["done"], bool):
            conn.close()
            return error(400, "done must be true or false")
        done = 1 if body["done"] else 0

    conn.execute(
        "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
        (title, done, task_id),
    )
    conn.commit()
    row = conn.execute(
        "SELECT id, title, done FROM tasks WHERE id = ?", (task_id,)
    ).fetchone()
    conn.close()
    return row_to_task(row)


@app.delete("/tasks/{task_id}", status_code=204, summary="Delete a task")
def delete_task(task_id: int):
    """Delete a task from the database."""
    conn = get_conn()
    row = conn.execute("SELECT id FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not row:
        conn.close()
        return error(404, "Task not found")
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return Response(status_code=204)
