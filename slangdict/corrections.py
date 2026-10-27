"""Apply versioned metadata fixes, requiring fresh independent checks afterward."""

from .pipeline import ROOT, read_rows, write_rows
import argparse, json
from pathlib import Path


def apply(path=None):
    fixes = {
        r["id"]: r
        for r in json.loads(
            (
                Path(path) if path else ROOT / "config/round3-variety-corrections.json"
            ).read_text()
        )
    }
    triage = {r["id"]: r for r in read_rows(ROOT / "work/gap-decisions.jsonl")}
    changed = 0
    for name in ["candidates", "attested"]:
        rows = read_rows(ROOT / ("work/" + name + ".jsonl"))
        for row in rows:
            fix = fixes.get(row["id"])
            if not fix:
                continue
            if row["spokenVariety"] == fix["to"]:
                continue
            assert (
                row["spokenVariety"] == fix["from"]
                and row["headword"] == fix["headword"]
            )
            row["spokenVariety"] = fix["to"]
            row.setdefault("metadataCorrections", []).append(fix)
            row.pop("scopeAudit", None)
            gate = row.get("coverageGate", {})
            if gate.get("correctionBasis") == "independent-scope-audit":
                row["coverageGate"] = triage.get(
                    row["id"], {"decision": "new-spelling"}
                )
            changed += 1
        write_rows(ROOT / ("work/" + name + ".jsonl"), rows)
    print({"metadataRowsUpdated": changed, "freshContextAndScopeChecksRequired": True})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input")
    apply(parser.parse_args().input)
