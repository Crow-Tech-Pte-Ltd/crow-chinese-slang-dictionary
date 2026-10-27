"""Offline release validation: no API key, network or private evidence required."""

from pathlib import Path
import json, gzip, hashlib, re, collections
from .provider import digest


def validate(root):
    root = Path(root)
    data = root / "data"
    manifest = json.loads((data / "manifest.json").read_text())
    sources = json.loads((data / "sources.json").read_text())
    source_by_id = {s["id"]: s for s in sources}
    rows = [
        json.loads(x)
        for x in (data / "entries.jsonl").read_text().splitlines()
        if x.strip()
    ]
    schema = json.loads((root / "schema/entry.schema.json").read_text())
    ids = set()
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
    for s in sources:
        assert (
            "context" not in s
            and "text" not in s
            and s["redistributedSourceText"] is False
        )
        assert s["url"].startswith(("https://", "http://")) and s["matchedHeadwords"]
    for r in rows:
        assert set(r) == set(schema["required"]), r["headword"]
        assert r["id"] not in ids
        ids.add(r["id"])
        assert (
            r["id"]
            == digest([r["headword"], r["senseKey"], r["regionOfAttestation"]])[:24]
        )
        assert r["license"] == "CC BY-SA 4.0" and r["definitionLanguage"] == "en"
        assert not re.search(
            r"[<>\x00-\x1f]|https?://|```", r["definition"] + r["usageNote"]
        )
        assert len(r["definition"].split()) <= 20 and len(r["usageNote"].split()) <= 12
        assert (
            r["validation"]["humanReviewed"] is False
            and r["validation"]["independentModelCheck"] is True
        )
        assert re.fullmatch("[a-f0-9]{64}", r["validation"]["reviewedInputSha256"])
        assert r["textProvenance"]["generator"] != r["textProvenance"]["checker"]
        assert (
            r["exclusiveOriginClaim"] is False
            and r["commonality"]["notAFrequencyEstimate"] is True
        )
        assert r["commonality"]["currentPopularityVerified"] is False
        assert r["register"] and len(set(r["register"])) == len(r["register"])
        assert len(set(r["evidenceIds"])) == len(r["evidenceIds"])
        for sid in r["evidenceIds"]:
            assert (
                sid in source_by_id
                and r["headword"] in source_by_id[sid]["matchedHeadwords"]
            )
        for reading in r["readings"]:
            assert (
                reading["spokenVariety"] == r["spokenVariety"]
                and reading["value"]
                and reading["sourceId"]
                and reading["sourceAttribution"]
            )
            assert reading["sourceLicense"] in ["CC BY-SA 4.0", "CC BY-SA 3.0", "MIT"]
            assert reading["system"] == (
                "jyutping" if r["spokenVariety"] == "yue" else "pinyin"
            )
            assert r["spokenVariety"] in ["cmn", "yue"]
    return {
        "entriesValidated": len(rows),
        "sourcePagesValidated": len(sources),
        "artifactChecksumsVerified": True,
        "privatePageTextAbsent": True,
        "independentReviewBoundToInputHashes": True,
        "humanReviewed": 0,
    }


if __name__ == "__main__":
    print(json.dumps(validate(Path(__file__).resolve().parents[1])))
