from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = ROOT / "artifacts" / "expected" / "hw3-top10.json"
ACTUAL = ROOT / "artifacts" / "results" / "parallel-top10.json"


def main() -> None:
    expected = json.loads(EXPECTED.read_text(encoding="utf-8"))["top10"]
    if not ACTUAL.exists():
        output = subprocess.check_output(
            ["kubectl", "-n", "lab5", "logs", "job/pairs-reduce"], text=True
        )
        actual_doc = json.loads(output)
        ACTUAL.parent.mkdir(parents=True, exist_ok=True)
        ACTUAL.write_text(json.dumps(actual_doc, ensure_ascii=False, indent=2), encoding="utf-8")
    actual = json.loads(ACTUAL.read_text(encoding="utf-8"))["top10"]
    if actual != expected:
        raise SystemExit("FAIL: Kubernetes top-10 differs from homework 3")
    print("PASS: Kubernetes top-10 exactly matches homework 3 (skills and counts)")


if __name__ == "__main__":
    main()
