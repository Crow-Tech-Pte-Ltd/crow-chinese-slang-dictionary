"""Offline validation for the distributable corpus, requiring no credentials."""

from pathlib import Path
import json, gzip, hashlib, re
from .provider import digest


def validate(root):
    root = Path(root)
    data = root / "data"
    manifest = json.loads((data / "manifest.json").read_text())
    sources = json.loads((data / "sources.json").read_text())
    by_source = {s["id"]: s for s in sources}
    rows = [
        json.loads(line)
        for line in (data / "entries.jsonl").read_text().splitlines()
        if line
    ]
    by_id = {r["id"]: r for r in rows}
    schema = json.loads((root / "schema/entry.schema.json").read_text())
    assert len(by_id) == len(rows) and len(by_source) == len(sources)
    for name, info in manifest["artifacts"].items():
        body = (data / name).read_bytes()
        assert (
            len(body) == info["bytes"]
            and hashlib.sha256(body).hexdigest() == info["sha256"]
        ), name
    assert (
        gzip.decompress((data / "entries.jsonl.gz").read_bytes())
        == (data / "entries.jsonl").read_bytes()
    )
    assert (
        len(rows) == manifest["entries"]
        and len(sources) == manifest["sourcePages"]
        and len({r["headword"] for r in rows}) == manifest["headwords"]
    )
    for source in sources:
        assert (
            "text" not in source
            and "context" not in source
            and source["redistributedSourceText"] is False
        )
        assert (
            source["url"].startswith(("https://", "http://"))
            and source["matchedHeadwords"]
        )
    from .scope import load_policy, exclusion
    policy=load_policy(root)
    for row in rows:
        assert exclusion(row,policy) is None, 'Out-of-scope sense in accepted corpus: '+row['headword']
    if 'pronunciationEvidence' in manifest:
        readings=[json.loads(l) for l in (data/'pronunciations.jsonl').read_text().splitlines() if l]
        unresolved=[json.loads(l) for l in (data/'pronunciation-unresolved.jsonl').read_text().splitlines() if l]
        a={r['entryId'] for r in readings};b={r['entryId'] for r in unresolved}
        assert a.isdisjoint(b) and a|b==set(by_id)
        assert len(readings)==manifest['pronunciationEvidence']['resolvedRecords'] and len(unresolved)==manifest['pronunciationEvidence']['unresolvedOrUnsupportedRecords']
    imported = 0
    relations = 0
    for row in rows:
        assert set(schema["required"]) <= set(row) <= set(schema["properties"]), row[
            "headword"
        ]
        assert (
            row["id"]
            == digest([row["headword"], row["senseKey"], row["regionOfAttestation"]])[
                :24
            ]
        )
        assert row["license"] == "CC BY-SA 4.0" and row["definitionLanguage"] == "en"
        assert not re.search(
            r"[<>\x00-\x1f]|https?://|```", row["definition"] + row["usageNote"]
        )
        assert (
            row["validation"]["humanReviewed"] is False
            and row["validation"]["independentModelCheck"] is True
        )
        assert re.fullmatch("[a-f0-9]{64}", row["validation"]["reviewedInputSha256"])
        assert row["textProvenance"]["generator"] != row["textProvenance"]["checker"]
        assert (
            row["exclusiveOriginClaim"] is False
            and row["commonality"]["notAFrequencyEstimate"] is True
            and row["commonality"]["currentPopularityVerified"] is False
        )
        assert row["register"] and len(set(row["register"])) == len(row["register"])
        assert (
            len(set(row["evidenceIds"])) == len(row["evidenceIds"])
            and row["evidenceIds"]
        )
        for sid in row["evidenceIds"]:
            assert (
                sid in by_source
                and row["headword"] in by_source[sid]["matchedHeadwords"]
            )
        if row.get("entryKind") == "source-import":
            imported += 1
            s = row["sourceImport"]
            assert (
                s["sourceLicense"] == "CC BY-SA 4.0"
                and s["sourceAttribution"]
                and s["sourceSnapshot"]
            )
            assert re.fullmatch("[a-f0-9]{64}", s["sourceFileSha256"])
            assert digest(row["definition"]) == s["sourceDefinitionSha256"]
            assert (
                digest(s["selectionInput"])
                == s["selectionInputSha256"]
                == row["validation"]["reviewedInputSha256"]
            )
            assert row["textProvenance"]["kind"] == "attributed-source-import"
            assert (
                row["sourceImport"]["sourceHeadword"] == s["selectionInput"]["headword"]
            )
            assert s["attestedSpellings"][row["headword"]] == row["spellingKind"]
        else:
            assert (
                len(row["definition"].split()) <= 20
                and len(row["usageNote"].split()) <= 12
            )
        for reading in row["readings"]:
            assert (
                reading["spokenVariety"] == row["spokenVariety"]
                and reading["value"]
                and reading["sourceId"]
                and reading["sourceAttribution"]
            )
            assert reading["sourceLicense"] in ["CC BY-SA 4.0", "CC BY-SA 3.0", "MIT"]
            assert row["spokenVariety"] in ["cmn", "yue"] and reading["system"] == (
                "jyutping" if row["spokenVariety"] == "yue" else "pinyin"
            )
        for relation in row.get("formRelations", []):
            target = by_id[relation["targetId"]]
            relations += 1
            assert (
                target["headword"] == relation["targetHeadword"]
                and row["headword"] != target["headword"]
            )
            assert target["senseGroupId"] == row["senseGroupId"]
            assert relation["type"] in [
                "script-variant",
                "homophonic-variant",
                "alternate-spelling",
                "abbreviation",
            ]
            assert set(relation["evidenceIds"]) <= set(by_source)
            assert any(
                back["targetId"] == row["id"] and back["type"] == relation["type"]
                for back in target["formRelations"]
            )
            if relation["basis"] == "explicit-source-script-form":
                assert (
                    row["sourceImport"]["sourceSenseId"]
                    == target["sourceImport"]["sourceSenseId"]
                )
                assert (
                    row["sourceImport"]["sourceDefinitionSha256"]
                    == target["sourceImport"]["sourceDefinitionSha256"]
                )
            else:
                assert (
                    relation["basis"] == "independent-source-context-check"
                    and relation["humanReviewed"] is False
                )
                assert re.fullmatch("[a-f0-9]{64}", relation["reviewedInputSha256"])
    return {
        "entriesValidated": len(rows),
        "sourcePagesValidated": len(sources),
        "sourceImportedEntries": imported,
        "directedSpellingRelationsValidated": relations,
        "artifactChecksumsVerified": True,
        "privatePageTextAbsent": True,
        "importSelectionInputHashesVerified": True,
        "humanReviewed": 0,
    }


if __name__ == "__main__":
    print(json.dumps(validate(Path(__file__).resolve().parents[1])))
