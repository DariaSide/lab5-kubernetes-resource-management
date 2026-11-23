from __future__ import annotations

import argparse
import itertools
import json
import os
import resource
import time
from collections import Counter
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError


ENDPOINT = os.getenv("S3_ENDPOINT", "http://rustfs:9000")
ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "LAB5ACCESSKEY")
SECRET_KEY = os.getenv("S3_SECRET_KEY", "Lab5SecretKeyChangeMe2026")
BUCKET = os.getenv("S3_BUCKET", "hh-lake")
OBJECT_KEY = os.getenv("S3_OBJECT_KEY", "input/devops_vacancies.ndjson")
DATASET = Path(os.getenv("DATASET", "/app/data/devops_vacancies.ndjson"))


def s3_client():
    return boto3.client(
        "s3",
        endpoint_url=ENDPOINT,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        region_name="us-east-1",
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
            retries={"max_attempts": 8, "mode": "standard"},
        ),
    )


def ensure_bucket(client) -> None:
    try:
        client.head_bucket(Bucket=BUCKET)
    except ClientError:
        client.create_bucket(Bucket=BUCKET)


def peak_mib() -> float:
    # ru_maxrss is KiB on Linux (the container runtime used by Kubernetes).
    return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 2)


def memory_probe() -> list[bytearray]:
    mib = int(os.getenv("MEMORY_PROBE_MIB", "0"))
    blocks = []
    for _ in range(mib):
        block = bytearray(1024 * 1024)
        block[0] = 1
        blocks.append(block)
    if mib:
        print(json.dumps({"event": "memory_probe", "allocated_mib": mib, "peak_rss_mib": peak_mib()}), flush=True)
    return blocks


def skills(row: dict) -> list[str]:
    raw = row.get("skills")
    if isinstance(raw, list):
        values = raw
    else:
        values = str(row.get("key_skills") or "").split(";")
    seen: dict[str, str] = {}
    for value in values:
        cleaned = " ".join(str(value).strip().split())
        if cleaned:
            seen.setdefault(cleaned.casefold(), cleaned)
    return [seen[key] for key in sorted(seen)]


def count_pairs(payload: bytes, part: int = 0, parts: int = 1) -> tuple[int, int, Counter]:
    rows = 0
    selected = 0
    counts: Counter[tuple[str, str]] = Counter()
    for index, line in enumerate(payload.splitlines()):
        if not line.strip():
            continue
        rows += 1
        if index % parts != part:
            continue
        selected += 1
        row_skills = skills(json.loads(line))
        counts.update(itertools.combinations(row_skills, 2))
    return rows, selected, counts


def encoded_counts(counts: Counter) -> list[dict]:
    return [
        {"skills": list(pair), "count": count}
        for pair, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def load_object(client) -> bytes:
    return client.get_object(Bucket=BUCKET, Key=OBJECT_KEY)["Body"].read()


def upload() -> None:
    client = s3_client()
    ensure_bucket(client)
    client.upload_file(str(DATASET), BUCKET, OBJECT_KEY, ExtraArgs={"ContentType": "application/x-ndjson"})
    head = client.head_object(Bucket=BUCKET, Key=OBJECT_KEY)
    print(json.dumps({
        "event": "uploaded",
        "uri": f"s3://{BUCKET}/{OBJECT_KEY}",
        "bytes": head["ContentLength"],
        "etag": head["ETag"],
    }, ensure_ascii=False), flush=True)


def standalone() -> None:
    retained = memory_probe()
    client = s3_client()
    payload = load_object(client)
    rows, selected, counts = count_pairs(payload)
    result = {
        "event": "standalone_complete",
        "rows": rows,
        "selected_rows": selected,
        "unique_pairs": len(counts),
        "top10": encoded_counts(counts)[:10],
        "peak_rss_mib": peak_mib(),
    }
    ensure_bucket(client)
    client.put_object(
        Bucket=BUCKET,
        Key="results/standalone-top10.json",
        Body=json.dumps(result, ensure_ascii=False, indent=2).encode(),
        ContentType="application/json",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    time.sleep(int(os.getenv("HOLD_SECONDS", "0")))
    assert retained is not None


def map_part() -> None:
    retained = memory_probe()
    part = int(os.getenv("JOB_COMPLETION_INDEX", os.getenv("PART_INDEX", "0")))
    parts = int(os.getenv("TOTAL_PARTS", "4"))
    client = s3_client()
    payload = load_object(client)
    rows, selected, counts = count_pairs(payload, part=part, parts=parts)
    result = {
        "part": part,
        "parts": parts,
        "source_rows": rows,
        "selected_rows": selected,
        "unique_pairs": len(counts),
        "counts": [{"skills": list(pair), "count": count} for pair, count in sorted(counts.items())],
        "peak_rss_mib": peak_mib(),
    }
    key = f"partials/part-{part:05d}.json"
    client.put_object(Bucket=BUCKET, Key=key, Body=json.dumps(result, ensure_ascii=False).encode(), ContentType="application/json")
    print(json.dumps({k: result[k] for k in ("part", "parts", "source_rows", "selected_rows", "unique_pairs", "peak_rss_mib")} | {"key": key}, ensure_ascii=False), flush=True)
    assert retained is not None


def reduce_parts() -> None:
    parts = int(os.getenv("TOTAL_PARTS", "4"))
    client = s3_client()
    deadline = time.time() + int(os.getenv("WAIT_SECONDS", "180"))
    documents = []
    while time.time() < deadline:
        documents = []
        try:
            for part in range(parts):
                body = client.get_object(Bucket=BUCKET, Key=f"partials/part-{part:05d}.json")["Body"].read()
                documents.append(json.loads(body))
            break
        except ClientError:
            time.sleep(2)
    if len(documents) != parts:
        raise RuntimeError(f"expected {parts} partial files, found {len(documents)}")
    counts: Counter[tuple[str, str]] = Counter()
    selected_rows = 0
    peaks = []
    for document in documents:
        selected_rows += document["selected_rows"]
        peaks.append(document["peak_rss_mib"])
        for item in document["counts"]:
            counts[tuple(item["skills"])] += item["count"]
    result = {
        "event": "parallel_reduce_complete",
        "parts": parts,
        "rows": selected_rows,
        "unique_pairs": len(counts),
        "mapper_peak_rss_mib": peaks,
        "top10": encoded_counts(counts)[:10],
        "peak_rss_mib": peak_mib(),
    }
    client.put_object(
        Bucket=BUCKET,
        Key="results/parallel-top10.json",
        Body=json.dumps(result, ensure_ascii=False, indent=2).encode(),
        ContentType="application/json",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)


def burn_cpu() -> None:
    duration = int(os.getenv("DURATION_SECONDS", "600"))
    deadline = time.time() + duration
    value = 1
    while time.time() < deadline:
        value = (value * 1664525 + 1013904223) & 0xFFFFFFFF
    print(json.dumps({"event": "cpu_burn_complete", "value": value}))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("upload", "standalone", "map", "reduce", "burn-cpu"))
    args = parser.parse_args()
    {
        "upload": upload,
        "standalone": standalone,
        "map": map_part,
        "reduce": reduce_parts,
        "burn-cpu": burn_cpu,
    }[args.command]()


if __name__ == "__main__":
    main()

