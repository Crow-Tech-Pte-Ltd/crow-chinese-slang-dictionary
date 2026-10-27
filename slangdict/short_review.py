"""Retry only unresolved lexical selections, with exact short-reference mapping."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from .pipeline import ROOT, CHECKER, read_rows, write_rows, save
from .provider import Client, digest, output
from .expand import SYSTEM, selection_data


def checker_results():
    result = {}
    for name in [
        "lexical-checker.jsonl",
        "lexical-checker-recovered.jsonl",
        "lexical-checker-short.jsonl",
    ]:
        for row in read_rows(ROOT / "work" / name):
            result[row["id"]] = row
    return result


def resolve_decisions(decisions, refs):
    if not isinstance(decisions, list):
        return []
    counts = {}
    for d in decisions:
        if isinstance(d, dict):
            ref = d.get("id")
            counts[ref] = counts.get(ref, 0) + 1
    result = []
    for d in decisions:
        if not isinstance(d, dict):
            continue
        ref = d.get("id")
        if ref not in refs or counts[ref] != 1:
            continue
        original = refs[ref]
        if d.get("headword") != original["headword"]:
            continue
        if type(d.get("keep")) is not bool or d.get("level") not in [
            "general-common",
            "community-common",
            "attested-variant",
            "niche",
            "uncertain",
        ]:
            continue
        result.append(
            {
                **d,
                "id": original["id"],
                "keep": d["keep"]
                and d["level"]
                in ["general-common", "community-common", "attested-variant"],
                "inputSha256": digest(selection_data(original)),
            }
        )
    return result


def run(client):
    first = {r["id"]: r for r in read_rows(ROOT / "work/lexical-generator.jsonl")}
    results = checker_results()
    rows = [
        r
        for r in read_rows(ROOT / "work/lexical-candidates.jsonl")
        if first.get(r["id"], {}).get("keep") is True
        and results.get(r["id"], {}).get("inputSha256") != digest(selection_data(r))
    ]
    new = {r["id"]: r for r in read_rows(ROOT / "work/lexical-checker-short.jsonl")}
    batches = [rows[i : i + 24] for i in range(0, len(rows), 24)]

    def one(batch):
        refs = {f"r{i:02d}": r for i, r in enumerate(batch)}
        items = [{**selection_data(r), "id": ref} for ref, r in refs.items()]
        mapping = digest({ref: r["id"] for ref, r in refs.items()})
        prompt = (
            SYSTEM
            + " Use the supplied short ids verbatim. Also include headword in each decision, copied exactly from that item. Do not return long hashes."
        )
        response = client.call(
            "lexical-checker-short-ref:" + mapping[:24],
            CHECKER,
            prompt,
            {"items": items},
            max_tokens=16000,
        )
        decisions = resolve_decisions(output(response).get("decisions"), refs)
        return [
            {
                **d,
                "model": CHECKER,
                "responseId": response.get("id"),
                "referenceMapSha256": mapping,
                "humanReviewed": False,
            }
            for d in decisions
        ]

    errors = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(one, b): b for b in batches}
        for f in as_completed(futures):
            try:
                for d in f.result():
                    new[d["id"]] = d
                    results[d["id"]] = d
                write_rows(
                    ROOT / "work/lexical-checker-short.jsonl",
                    sorted(new.values(), key=lambda r: r["id"]),
                )
            except Exception as e:
                errors.append(
                    {"ids": [r["id"] for r in futures[f]], "error": type(e).__name__}
                )
    held = [r["id"] for r in rows if r["id"] not in results]
    report = {
        "attemptedMissing": len(rows),
        "recovered": len(new),
        "remainingUnreviewed": held,
        "errors": errors,
        "budget": client.summary(),
    }
    save(ROOT / "work/lexical-short-report.json", report)
    print(report)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--key-file", required=True)
    a = p.parse_args()
    run(Client(ROOT, a.key_file, 8))
