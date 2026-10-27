"""Recover exact valid decisions from completed cached batches; never guess ids."""

from pathlib import Path
import argparse, collections, json, sqlite3
from .pipeline import ROOT, GENERATOR, CHECKER, read_rows, write_rows, save
from .provider import make_payload, digest, output
from .expand import SYSTEM, selection_data

LEVELS = {
    "general-common",
    "community-common",
    "attested-variant",
    "niche",
    "uncertain",
}


def valid_decisions(obj, wanted):
    items = obj.get("decisions", []) if isinstance(obj, dict) else []
    if isinstance(items, dict) and all(
        isinstance(v, dict) and v.get("id") == k for k, v in items.items()
    ):
        items = list(items.values())
    if not isinstance(items, list):
        return [], list(wanted)
    counts = collections.Counter(d.get("id") for d in items if isinstance(d, dict))
    valid = []
    for d in items:
        if not isinstance(d, dict) or d.get("id") not in wanted or counts[d["id"]] != 1:
            continue
        if type(d.get("keep")) is not bool or d.get("level") not in LEVELS:
            continue
        valid.append(d)
    return valid, sorted(set(wanted) - {d["id"] for d in valid})


def recover(role):
    rows = read_rows(ROOT / "work/lexical-candidates.jsonl")
    if role == "checker":
        first = {d["id"]: d for d in read_rows(ROOT / "work/lexical-generator.jsonl")}
        rows = [r for r in rows if first.get(r["id"], {}).get("keep") is True]
    model = GENERATOR if role == "generator" else CHECKER
    max_tokens = 6500 if role == "generator" else 20000
    found = {}
    issues = []
    db = sqlite3.connect((ROOT / "work/budget.sqlite").as_uri() + "?mode=ro", uri=True)
    for at in range(0, len(rows), 40):
        batch = rows[at : at + 40]
        data = [selection_data(r) for r in batch]
        hashes = {r["id"]: digest(r) for r in data}
        phase = "lexical-" + role + ":" + digest([r["id"] for r in batch])[:20]
        payload = make_payload(model, SYSTEM, {"items": data}, max_tokens=max_tokens)
        fp = digest({"version": "crow-slang-v1", "phase": phase, "payload": payload})
        saved = db.execute(
            "SELECT state,path FROM requests WHERE id=?", (fp,)
        ).fetchone()
        if not saved or saved[0] != "completed":
            continue
        response = json.loads(Path(saved[1]).read_text())
        if response.get("model") != model:
            raise ValueError("cached-model-mismatch")
        try:
            decisions, missing = valid_decisions(output(response), set(hashes))
        except (ValueError, TypeError):
            issues.append(
                {
                    "batch": at // 40,
                    "reason": "nonfinal-or-invalid-json",
                    "ids": list(hashes),
                }
            )
            continue
        for d in decisions:
            found[d["id"]] = {
                **d,
                "keep": d["keep"]
                and d["level"]
                in ["general-common", "community-common", "attested-variant"],
                "model": model,
                "responseId": response.get("id"),
                "inputSha256": hashes[d["id"]],
                "recoveredFromExactCachedRequest": True,
                "partialBatch": bool(missing),
                "humanReviewed": False,
            }
        if missing:
            issues.append(
                {
                    "batch": at // 40,
                    "reason": "unknown-missing-or-duplicate-ids-held",
                    "ids": missing,
                }
            )
    db.close()
    write_rows(
        ROOT / ("work/lexical-" + role + "-recovered.jsonl"),
        sorted(found.values(), key=lambda d: d["id"]),
    )
    report = {
        "role": role,
        "recoveredDecisions": len(found),
        "selected": sum(x["keep"] for x in found.values()),
        "networkRequests": 0,
        "unknownIdsWereNotGuessed": True,
        "heldRows": sum(len(x["ids"]) for x in issues),
        "issues": issues,
    }
    save(ROOT / ("work/lexical-" + role + "-recovery-report.json"), report)
    print(json.dumps({k: v for k, v in report.items() if k != "issues"}))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--role", choices=["generator", "checker"], default="checker")
    recover(p.parse_args().role)
