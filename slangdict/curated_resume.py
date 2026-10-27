"""Recover partial paid review batches and retry only undecided short references."""

import argparse, collections, json, sqlite3
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from .pipeline import ROOT, CHECKER, TODAY, REVIEW, read_rows, write_rows, review_data
from .provider import Client, make_payload, digest, output

FIELDS = [
    "supported",
    "senseSupported",
    "communityUseSupported",
    "regionSupported",
    "registerAdequate",
]


def decisions(response, refs, short=False):
    obj = output(response)
    items = obj.get("reviews", [])
    if isinstance(items, dict) and all(
        isinstance(v, dict) and v.get("id") == k for k, v in items.items()
    ):
        items = list(items.values())
    if not isinstance(items, list):
        return []
    counts = collections.Counter(r.get("id") for r in items if isinstance(r, dict))
    result = []
    for d in items:
        if not isinstance(d, dict) or d.get("id") not in refs or counts[d["id"]] != 1:
            continue
        row = refs[d["id"]]
        if short and "headword" in d and d["headword"] != row["headword"]:
            continue
        if not all(type(d.get(k)) is bool for k in FIELDS):
            continue
        result.append(
            {
                **d,
                "id": row["id"],
                "status": "machine-checked" if all(d[k] for k in FIELDS) else "held",
                "checkerModel": CHECKER,
                "reviewResponseId": response.get("id"),
                "checkedAt": TODAY,
                "humanReviewed": False,
                "reviewedInputSha256": digest(review_data(row)),
            }
        )
    return result


def run(client):
    rows = [r for r in read_rows(ROOT / "work/attested.jsonl") if r["evidence"]]
    results = {r["id"]: r for r in read_rows(ROOT / "work/reviews.jsonl")}

    def missing():
        return [
            r
            for r in rows
            if results.get(r["id"], {}).get("reviewedInputSha256")
            != digest(review_data(r))
        ]

    pending = missing()
    db = sqlite3.connect((ROOT / "work/budget.sqlite").as_uri() + "?mode=ro", uri=True)
    recovered = 0
    for at in range(0, len(pending), 8):
        batch = pending[at : at + 8]
        data = [review_data(r) for r in batch]
        phase = "review:" + digest([r["id"] for r in batch])[:20]
        payload = make_payload(CHECKER, REVIEW, {"candidates": data}, max_tokens=16000)
        fp = digest({"version": "crow-slang-v1", "phase": phase, "payload": payload})
        saved = db.execute(
            "SELECT state,path FROM requests WHERE id=?", (fp,)
        ).fetchone()
        if not saved or saved[0] != "completed":
            continue
        response = json.loads(Path(saved[1]).read_text())
        if response.get("model") != CHECKER:
            raise ValueError("model-mismatch")
        try:
            for r in decisions(response, {r["id"]: r for r in batch}):
                results[r["id"]] = r
                recovered += 1
        except (ValueError, TypeError):
            pass
    db.close()
    write_rows(
        ROOT / "work/reviews.jsonl", sorted(results.values(), key=lambda r: r["id"])
    )
    pending = missing()
    errors = []

    def one(batch):
        refs = {f"r{i:02d}": r for i, r in enumerate(batch)}
        data = [{**review_data(r), "id": ref} for ref, r in refs.items()]
        prompt = (
            REVIEW
            + " Return the short ids verbatim and include a headword field copied exactly for each item. Never return long hashes."
        )
        phase = "review-short:" + digest([review_data(r) for r in batch])[:24]
        response = client.call(
            phase, CHECKER, prompt, {"candidates": data}, max_tokens=16000
        )
        return decisions(response, refs, True)

    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [
            pool.submit(one, pending[i : i + 8]) for i in range(0, len(pending), 8)
        ]
        for f in as_completed(futures):
            try:
                for r in f.result():
                    results[r["id"]] = r
                write_rows(
                    ROOT / "work/reviews.jsonl",
                    sorted(results.values(), key=lambda r: r["id"]),
                )
            except Exception as e:
                errors.append(type(e).__name__)
    print(
        {
            "cachedDecisionsRecovered": recovered,
            "shortReferenceRetryItems": len(pending),
            "unresolved": len(missing()),
            "errors": errors,
        },
        flush=True,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--key-file", required=True)
    a = p.parse_args()
    run(Client(ROOT, a.key_file, 8))
