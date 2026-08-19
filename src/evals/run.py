"""Run the 8 eval cases against POST /triage (async jobs) and print a score."""
import json
import os
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

CASES = Path(__file__).with_name("cases.json")
BASE = os.getenv("EVAL_BASE_URL", "http://127.0.0.1:8000")


def wait_for_result(client: httpx.Client, job_id: str, timeout: float = 90.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = client.get(f"{BASE}/triage/jobs/{job_id}")
        r.raise_for_status()
        data = r.json()
        if data["status"] == "succeeded":
            return data["result"]
        if data["status"] == "failed":
            raise RuntimeError(data.get("error", "job failed"))
        time.sleep(0.5)
    raise TimeoutError(f"job {job_id} did not finish in time")


def main() -> None:
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    ok = 0
    failed = []
    with httpx.Client(timeout=60.0) as client:
        for case in cases:
            r = client.post(f"{BASE}/triage", json={"text": case["text"]})
            if r.status_code != 202:
                failed.append({"id": case["id"], "error": r.text})
                continue
            try:
                result = wait_for_result(client, r.json()["job_id"])
            except Exception as exc:
                failed.append({"id": case["id"], "error": str(exc)})
                continue
            got = result.get("category")
            if got == case["expected_category"]:
                ok += 1
            else:
                failed.append(
                    {
                        "id": case["id"],
                        "expected": case["expected_category"],
                        "got": got,
                    }
                )
    total = len(cases)
    pct = round(100 * ok / total) if total else 0
    print(f"matches: {ok}/{total} ({pct}%) on key field: category")
    if failed:
        print("failed cases:")
        for item in failed:
            print(" ", item)
    else:
        print("all cases passed")


if __name__ == "__main__":
    main()
    sys.exit(0)
