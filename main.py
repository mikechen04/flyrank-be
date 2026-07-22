from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

app = FastAPI(title="Task API", version="1.0")

tasks = [
    {"id": 1, "title": "Learn FastAPI", "done": False},
    {"id": 2, "title": "Build a CRUD API", "done": False},
    {"id": 3, "title": "Push to GitHub", "done": True},
]
next_id = 4


def find_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task
    return None


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
    """Return all tasks."""
    return tasks


@app.get("/tasks/{task_id}", summary="Get one task")
def get_task(task_id: int):
    """Get a task by id."""
    task = find_task(task_id)
    return task if task else error(404, f"Task {task_id} not found")


@app.post("/tasks", status_code=201, summary="Create a task")
async def create_task(request: Request):
    """Create a new task. Body needs a title."""
    global next_id
    try:
        body = await request.json()
    except Exception:
        return error(400, "body must be valid JSON")
    title = body.get("title") if isinstance(body, dict) else None
    if not title or not str(title).strip():
        return error(400, "title is required and must not be empty")
    task = {"id": next_id, "title": str(title).strip(), "done": False}
    next_id += 1
    tasks.append(task)
    return task


@app.put("/tasks/{task_id}", summary="Update a task")
async def update_task(task_id: int, request: Request):
    """Update a task's title and/or done."""
    task = find_task(task_id)
    if not task:
        return error(404, f"Task {task_id} not found")
    try:
        body = await request.json()
    except Exception:
        return error(400, "body must be valid JSON")
    if not isinstance(body, dict) or ("title" not in body and "done" not in body):
        return error(400, "body must include title and/or done")
    if "title" in body:
        if not body["title"] or not str(body["title"]).strip():
            return error(400, "title must not be empty")
        task["title"] = str(body["title"]).strip()
    if "done" in body:
        if not isinstance(body["done"], bool):
            return error(400, "done must be true or false")
        task["done"] = body["done"]
    return task


@app.delete("/tasks/{task_id}", status_code=204, summary="Delete a task")
def delete_task(task_id: int):
    """Delete a task by id."""
    task = find_task(task_id)
    if not task:
        return error(404, f"Task {task_id} not found")
    tasks.remove(task)
    return Response(status_code=204)
