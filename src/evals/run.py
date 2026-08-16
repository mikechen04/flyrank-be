"""Run the 8 eval cases against POST /triage and print a score."""
import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

CASES = Path(__file__).with_name("cases.json")
BASE = os.getenv("EVAL_BASE_URL", "http://127.0.0.1:8000")


def main() -> None:
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    ok = 0
    failed = []
    for case in cases:
        r = httpx.post(f"{BASE}/triage", json={"text": case["text"]}, timeout=60.0)
        if r.status_code != 200:
            failed.append({"id": case["id"], "error": r.text})
            continue
        got = r.json().get("category")
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
