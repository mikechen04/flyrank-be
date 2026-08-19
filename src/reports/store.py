"""In-memory report store (clears on restart — that is expected)."""

reports: dict[str, dict] = {}
