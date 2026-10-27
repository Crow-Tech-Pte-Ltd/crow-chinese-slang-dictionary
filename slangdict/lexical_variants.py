"""Resolve explicit source alternative forms against exact released senses."""

import argparse, collections, re
from concurrent.futures import ThreadPoolExecutor, as_completed
from .pipeline import ROOT, CHECKER, read_rows, write_rows, save
from .provider import Client, digest, output
from .variants import SYSTEM


def proposals(rows):
    by_word = collections.defaultdict(dict)
    for r in rows:
        if r["entryKind"] == "source-import":
            by_word[r["headword"]][r["senseGroupId"]] = r
    units = []
    seen = set()
    for a in rows:
        if a["entryKind"] != "source-import" or a["spellingKind"] != "source-headword":
            continue
        if not re.search(
            r"(?:alternative form|pronunciation spelling|eye dialect|initialism|acronym)",
            a["definition"],
            re.I,
        ):
            continue
        choices = {}
        for alt in a["sourceImport"]["sourceAltOf"]:
            for word in re.split(r"\s*[/／]\s*", alt["word"]):
                for group, b in by_word.get(word, {}).items():
                    if (
                        a["spokenVariety"] == b["spokenVariety"]
                        and a["senseGroupId"] != group
                    ):
                        choices[group] = b
        if not choices or len(choices) > 12:
            continue
        group = a["senseGroupId"]
        if group in seen:
            continue
        seen.add(group)
        units.append(
            {"source": a, "targets": sorted(choices.values(), key=lambda r: r["id"])}
        )
    return units


def run(client):
    rows = read_rows(ROOT / "data/entries.jsonl")
    units = proposals(rows)
    existing = {
        r["family"]: r for r in read_rows(ROOT / "work/lexical-variant-reviews.jsonl")
    }

    def one(unit):
        a = unit["source"]
        members = [a] + unit["targets"]
        refs = {f"r{i:02d}": r for i, r in enumerate(members)}
        items = [
            {
                "ref": ref,
                "headword": r["headword"],
                "definition": r["definition"],
                "spokenVariety": r["spokenVariety"],
                "sourceAltOf": r["sourceImport"]["sourceAltOf"],
                "sourceTags": r["sourceImport"]["sourceTags"],
                "sourceUrl": r["sourceImport"]["sourceUrl"],
            }
            for ref, r in refs.items()
        ]
        sha = digest(items)
        family = (
            "lexical-"
            + digest([a["sourceImport"]["sourceSenseId"], a["definition"]])[:24]
        )
        if existing.get(family, {}).get("inputSha256") == sha:
            return existing[family]
        prompt = (
            SYSTEM
            + " Here evidence is openly licensed lexicographic sense records. r00 explicitly names an alternative form; select only r00-to-target pairs that resolve the SAME meaning. A source alternative-name synonym is not a spelling variant. Do not connect target senses to each other. An initialism may link its full expression. A polysemous target requires choosing the exact sense; abstain if ambiguous."
        )
        response = client.call(
            "lexical-form-relations:" + sha[:24],
            CHECKER,
            prompt,
            {"items": items},
            max_tokens=10000,
        )
        pairs = []
        seen = set()
        for p in output(response).get("pairs", []):
            if (
                not isinstance(p, dict)
                or p.get("supported") is not True
                or p.get("type")
                not in [
                    "script-variant",
                    "homophonic-variant",
                    "abbreviation",
                    "alternate-spelling",
                ]
            ):
                continue
            x, y = p.get("a"), p.get("b")
            if x not in refs or y not in refs or x == y or "r00" not in [x, y]:
                continue
            a, b = refs[x], refs[y]
            pair = tuple(sorted([a["id"], b["id"]]))
            if a["headword"] == b["headword"] or pair in seen:
                continue
            seen.add(pair)
            pairs.append(
                {
                    "a": a["id"],
                    "b": b["id"],
                    "type": p["type"],
                    "reason": str(p.get("reason", ""))[:240],
                }
            )
        return {
            "family": family,
            "inputSha256": sha,
            "reviewModel": CHECKER,
            "reviewResponseId": response.get("id"),
            "humanReviewed": False,
            "pairs": pairs,
            "candidateIds": [r["id"] for r in members],
        }

    errors = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(one, u): u for u in units}
        for f in as_completed(futures):
            try:
                row = f.result()
                existing[row["family"]] = row
                write_rows(
                    ROOT / "work/lexical-variant-reviews.jsonl",
                    sorted(existing.values(), key=lambda r: r["family"]),
                )
            except Exception as e:
                errors.append(
                    {"id": futures[f]["source"]["id"], "error": type(e).__name__}
                )
    print(
        {
            "proposedFamilies": len(units),
            "reviewedFamilies": len(existing),
            "pairs": sum(len(r["pairs"]) for r in existing.values()),
            "errors": errors,
        },
        flush=True,
    )
    save(
        ROOT / "work/lexical-variant-report.json",
        {
            "proposedFamilies": len(units),
            "reviewedFamilies": len(existing),
            "pairs": sum(len(r["pairs"]) for r in existing.values()),
            "errors": errors,
        },
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--key-file", required=True)
    a = p.parse_args()
    run(Client(ROOT, a.key_file, 8))
