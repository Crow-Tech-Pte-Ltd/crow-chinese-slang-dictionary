"""Verify an export against retained primary data and private review provenance."""

import argparse, collections, gzip, hashlib, json
from pathlib import Path
from .pipeline import ROOT, read_rows, review_data, save
from .provider import digest
from .expand import spelling_forms, selection_data
from .short_review import checker_results
from .social_evidence import social_page_kind


def audit(source):
    rows = read_rows(ROOT / "data/entries.jsonl")
    imports = [r for r in rows if r["entryKind"] == "source-import"]
    by_line = collections.defaultdict(list)
    for r in imports:
        by_line[r["sourceImport"]["sourceRowIndex"]].append(r)
    sha = hashlib.sha256()
    with Path(source).open("rb") as f:
        while chunk := f.read(1024 * 1024):
            sha.update(chunk)
    expected = json.loads((ROOT / "config/lexical-source.json").read_text())["sha256"]
    assert sha.hexdigest() == expected
    found = set()
    with gzip.open(source, "rt", encoding="utf-8") as f:
        for n, line in enumerate(f):
            if n not in by_line:
                continue
            primary = json.loads(line)
            forms = spelling_forms(primary)
            for row in by_line[n]:
                s = row["sourceImport"]
                sense = primary["senses"][s["sourceSenseIndex"]]
                gloss = "; ".join(
                    dict.fromkeys(sense.get("raw_glosses", sense["glosses"]))
                )
                clean = "; ".join(dict.fromkeys(sense["glosses"]))
                assert primary["word"] == s["sourceHeadword"]
                assert row["definition"] == gloss and row["headword"] in forms
                assert (
                    forms == s["attestedSpellings"]
                    and forms[row["headword"]] == row["spellingKind"]
                )
                assert (
                    s["sourceTags"] == sorted(sense["tags"])
                    and s["selectionInput"]["definition"] == clean
                )
                assert s["sourceFileSha256"] == expected
                found.add(row["id"])
    assert len(found) == len(imports)
    drafts = {r["id"]: r for r in read_rows(ROOT / "work/attested.jsonl")}
    reviews = {r["id"]: r for r in read_rows(ROOT / "work/reviews.jsonl")}
    for row in rows:
        if row["entryKind"] != "curated-summary":
            continue
        draft = drafts[row["id"]]
        review = reviews[row["id"]]
        assert (
            review["status"] == "machine-checked"
            and review["reviewedInputSha256"]
            == digest(review_data(draft))
            == row["validation"]["reviewedInputSha256"]
        )
        assert (
            row["definition"] == draft["definition"]
            and row["spokenVariety"] == draft["spokenVariety"]
        )
        assert all(
            social_page_kind(e["url"]) != "platform-index" for e in draft["evidence"]
        )
    proofs = read_rows(ROOT / "work/variant-reviews.jsonl") + read_rows(
        ROOT / "work/lexical-variant-reviews.jsonl"
    )
    verified = {
        (frozenset([p["a"], p["b"]]), p["type"], proof["inputSha256"])
        for proof in proofs
        for p in proof["pairs"]
    }
    for row in rows:
        for link in row["formRelations"]:
            if link["basis"] == "independent-source-context-check":
                assert (
                    frozenset([row["id"], link["targetId"]]),
                    link["type"],
                    link["reviewedInputSha256"],
                ) in verified
    generator = {r["id"]: r for r in read_rows(ROOT / "work/lexical-generator.jsonl")}
    checker = checker_results()
    lexical = read_rows(ROOT / "work/lexical-candidates.jsonl")
    assert all(
        generator.get(r["id"], {}).get("inputSha256") == digest(selection_data(r))
        for r in lexical
    )
    assert all(
        checker.get(r["id"], {}).get("inputSha256") == digest(selection_data(r))
        for r in lexical
        if generator[r["id"]]["keep"]
    )
    report = {
        "sourceSnapshotSha256Verified": True,
        "sourceImportedRecordsVerifiedAgainstPrimaryRows": len(imports),
        "curatedRecordsVerifiedAgainstCurrentContextReviews": len(rows) - len(imports),
        "allIndependentSpellingLinksHaveExactReviewProof": True,
        "allLexicalSelectionJobsResolved": True,
        "humanReviewed": 0,
    }
    save(ROOT / "reports/local-build-audit.json", report)
    print(json.dumps(report))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True)
    audit(p.parse_args().source)
