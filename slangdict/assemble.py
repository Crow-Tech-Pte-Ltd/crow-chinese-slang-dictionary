"""Build an attributed expansion without changing the published v0.1 artifacts."""

import collections, gzip, hashlib
from .pipeline import (
    ROOT,
    TODAY,
    GENERATOR,
    CHECKER,
    read_rows,
    write_rows,
    save,
    review_data,
    valid_candidate,
)
from .provider import canonical, digest
from .expand import selection_data
from .short_review import checker_results

REGISTER_TAGS = {
    "slang": "informal",
    "colloquial": "informal",
    "informal": "informal",
    "Internet": "internet",
    "internet": "internet",
    "vulgar": "vulgar",
    "derogatory": "derogatory",
    "offensive": "offensive",
    "sexual": "sexual",
    "humorous": "playful",
    "dated": "dated",
    "slur": "offensive",
    "regional": "regional",
    "dialectal": "regional",
}


def add_source(sources, evidence, word):
    sid = digest(evidence["url"])[:20]
    old = sources.get(sid, {})
    record = {k: v for k, v in evidence.items() if k != "context"}
    # Preserve stronger accessible evidence rather than replacing it with an excerpt.
    if old.get("attestationKind", "").startswith("fetched") and not record.get(
        "attestationKind", ""
    ).startswith("fetched"):
        record = {**record, **old}
    sources[sid] = {
        **old,
        **record,
        "id": sid,
        "matchedHeadwords": sorted(set(old.get("matchedHeadwords", []) + [word])),
        "redistributedSourceText": False,
    }
    sources[sid].setdefault(
        "license", "link-only; underlying page retains its copyright"
    )
    return sid


def source_record(row, word, spelling_kind, group, generator, checker, source_id):
    region = "+".join(row["regionLabels"]) or "source-region-unspecified"
    sense = (
        "wikt-"
        + digest([row["sourceSenseId"], row["definition"], row["sourceTags"]])[:16]
    )
    registers = sorted(
        {v for k, v in REGISTER_TAGS.items() if k in row["sourceTags"]}
    ) or ["informal"]
    if row["regionLabels"] or row["spokenVariety"] not in ["und", "cmn"]:
        registers = sorted(set(registers + ["regional"]))
    return {
        "id": digest([word, sense, region])[:24],
        "headword": word,
        "senseKey": sense,
        "definitionLanguage": "en",
        "definition": "; ".join(dict.fromkeys(row["rawGlosses"])),
        "usageNote": "Source labels retained; present-day popularity has not been measured.",
        "regionOfAttestation": region,
        "community": "Source-labelled Chinese informal usage",
        "exclusiveOriginClaim": False,
        "spokenVariety": row["spokenVariety"],
        "register": registers,
        "readings": [],
        "readingStatus": "unresolved-not-attested-for-this-sense",
        "existingDictionaryOverlap": {"status": "not-audited", "sourceIds": []},
        "commonality": {
            "status": "lexicographically-attested-machine-prioritized",
            "notAFrequencyEstimate": True,
            "currentPopularityVerified": False,
            "checkedAt": TODAY,
            "evidenceCount": 1,
            "selectionLevel": checker["level"],
        },
        "evidenceIds": [source_id],
        "textProvenance": {
            "kind": "attributed-source-import",
            "generator": GENERATOR,
            "checker": CHECKER,
            "modelRole": "Independent relevance selection only; models did not author this definition.",
            "selectionResponseId": generator["responseId"],
            "reviewResponseId": checker["responseId"],
        },
        "validation": {
            "status": "source-import-independently-selected",
            "humanReviewed": False,
            "independentModelCheck": True,
            "contextLevel": ["open-lexicon-record"],
            "reviewedInputSha256": checker["inputSha256"],
        },
        "license": "CC BY-SA 4.0",
        "entryKind": "source-import",
        "senseGroupId": group,
        "spellingKind": spelling_kind,
        "formRelations": [],
        "sourceImport": {
            k: row[k]
            for k in [
                "sourceSenseId",
                "sourceUrl",
                "sourceLicense",
                "sourceLicenseUrl",
                "sourceAttribution",
                "sourceSnapshot",
                "sourceFileSha256",
                "sourceRowIndex",
                "sourceSenseIndex",
                "sourceTags",
                "sourcePos",
                "sourceAltOf",
            ]
        }
        | {
            "sourceHeadword": row["headword"],
            "sourceDefinitionSha256": digest(
                "; ".join(dict.fromkeys(row["rawGlosses"]))
            ),
            "selectionInputSha256": digest(selection_data(row)),
            "selectionInput": selection_data(row),
            "attestedSpellings": row["spellings"],
        },
    }


def assemble():
    base = ROOT / "work/v0.1-base"
    base_rows = {r["id"]: r for r in read_rows(base / "entries.jsonl")}
    entries = {}
    sources = {}
    reviews = {r["id"]: r for r in read_rows(ROOT / "work/reviews.jsonl")}
    held = []
    for row in read_rows(ROOT / "work/attested.jsonl"):
        checked = reviews.get(row["id"], {})
        reason = None
        if not valid_candidate(row):
            reason = "invalid-draft-fields"
        elif not row["evidence"]:
            reason = "no-usable-literal-attestation"
        elif checked.get("reviewedInputSha256") != digest(review_data(row)):
            reason = "missing-or-stale-independent-review"
        elif checked.get("status") != "machine-checked":
            reason = checked.get("reason", "independent-review-held")
        if reason:
            held.append(
                {
                    "id": row["id"],
                    "headword": row["headword"],
                    "stage": "curated",
                    "reason": reason,
                }
            )
            continue
        evidence = sorted(
            {add_source(sources, e, row["headword"]) for e in row["evidence"]}
        )
        entries[row["id"]] = {
            "id": row["id"],
            "headword": row["headword"],
            "senseKey": row["senseKey"],
            "definitionLanguage": "en",
            "definition": row["definition"],
            "usageNote": row["usageNote"],
            "regionOfAttestation": row["regionId"],
            "community": row["community"],
            "exclusiveOriginClaim": False,
            "spokenVariety": row["spokenVariety"],
            "register": list(dict.fromkeys(row["register"])),
            "readings": [],
            "readingStatus": "unresolved-not-attested-for-this-sense",
            "existingDictionaryOverlap": {"status": "not-audited", "sourceIds": []},
            "commonality": {
                "status": "source-attested-community-use",
                "notAFrequencyEstimate": True,
                "currentPopularityVerified": False,
                "checkedAt": TODAY,
                "evidenceCount": len(evidence),
            },
            "evidenceIds": evidence,
            "textProvenance": {
                "kind": "AI-assisted-original-summary",
                "generator": GENERATOR,
                "checker": CHECKER,
                "draftResponseId": row["discoveryResponseId"],
                "reviewResponseId": checked["reviewResponseId"],
            },
            "validation": {
                "status": "machine-checked-source-context",
                "humanReviewed": False,
                "independentModelCheck": True,
                "contextLevel": sorted({e["attestationKind"] for e in row["evidence"]}),
                "reviewedInputSha256": checked["reviewedInputSha256"],
            },
            "license": "CC BY-SA 4.0",
            "entryKind": "curated-summary",
            "senseGroupId": "sense-" + row["id"],
            "spellingKind": "attested-headword",
            "formRelations": [],
        }
        previous = base_rows.get(row["id"])
        if previous and previous["spokenVariety"] == row["spokenVariety"]:
            for key in ["readings", "readingStatus", "existingDictionaryOverlap"]:
                entries[row["id"]][key] = previous[key]
    # Each explicit script form is a distinct lookup record with a shared source sense.
    generator = {r["id"]: r for r in read_rows(ROOT / "work/lexical-generator.jsonl")}
    checker = checker_results()
    for row in read_rows(ROOT / "work/lexical-candidates.jsonl"):
        uid = row["id"]
        sha = digest(selection_data(row))
        if not all(
            m.get(uid, {}).get("keep") is True and m[uid].get("inputSha256") == sha
            for m in [generator, checker]
        ):
            held.append(
                {
                    "id": uid,
                    "headword": row["headword"],
                    "stage": "source-selection",
                    "reason": "independent-selection-held"
                    if uid in checker or not generator.get(uid, {}).get("keep")
                    else "independent-selection-unresolved",
                }
            )
            continue
        group = (
            "source-sense-"
            + digest([row["sourceSenseId"], row["definition"], row["sourceTags"]])[:24]
        )
        siblings = []
        for word, kind in row["spellings"].items():
            sid = add_source(
                sources,
                {
                    "url": row["sourceUrl"],
                    "attestationKind": "open-lexicon-record",
                    "checkedAt": TODAY,
                    "literalMentionConfirmed": True,
                    "license": row["sourceLicense"],
                    "licenseUrl": row["sourceLicenseUrl"],
                    "attribution": row["sourceAttribution"],
                    "snapshot": row["sourceSnapshot"],
                    "sourceFileSha256": row["sourceFileSha256"],
                    "definitionsRedistributedUnderOpenLicense": True,
                },
                word,
            )
            record = source_record(
                row, word, kind, group, generator[uid], checker[uid], sid
            )
            entries[record["id"]] = record
            siblings.append(record)
        for a in siblings:
            for b in siblings:
                if a["id"] != b["id"]:
                    a["formRelations"].append(
                        {
                            "targetId": b["id"],
                            "targetHeadword": b["headword"],
                            "type": "script-variant",
                            "evidenceIds": [sid],
                            "basis": "explicit-source-script-form",
                        }
                    )
    # Merge groups only along independently checked, sense-specific variant edges.
    parent = {i: i for i in entries}
    groups = {}
    for i, r in entries.items():
        groups.setdefault(r["senseGroupId"], []).append(i)
    for members in groups.values():
        root = min(members)
        for i in members:
            parent[i] = root

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for review in read_rows(ROOT / "work/variant-reviews.jsonl") + read_rows(
        ROOT / "work/lexical-variant-reviews.jsonl"
    ):
        for pair in review["pairs"]:
            a, b = pair["a"], pair["b"]
            if a not in entries or b not in entries:
                continue
            for x, y in [(a, b), (b, a)]:
                entries[x]["formRelations"].append(
                    {
                        "targetId": y,
                        "targetHeadword": entries[y]["headword"],
                        "type": pair["type"],
                        "evidenceIds": sorted(
                            set(entries[x]["evidenceIds"] + entries[y]["evidenceIds"])
                        ),
                        "basis": "independent-source-context-check",
                        "reviewModel": review["reviewModel"],
                        "reviewResponseId": review["reviewResponseId"],
                        "reviewedInputSha256": review["inputSha256"],
                        "humanReviewed": False,
                    }
                )
            ra, rb = find(a), find(b)
            parent[max(ra, rb)] = min(ra, rb)
    for i in entries:
        entries[i]["senseGroupId"] = "sense-" + find(i)
    published = sorted(entries.values(), key=lambda r: r["id"])
    write_rows(ROOT / "data/entries.jsonl", published)
    body = (ROOT / "data/entries.jsonl").read_bytes()
    (ROOT / "data/entries.jsonl.gz").write_bytes(gzip.compress(body, mtime=0))
    save(ROOT / "data/sources.json", sorted(sources.values(), key=lambda r: r["id"]))
    write_rows(ROOT / "work/held-v0.2.jsonl", held)
    notice = (ROOT / "data/NOTICE.txt").read_text().replace("v0.1.0", "v0.2.0")
    marker = "\nOpenly licensed definition imports (v0.2.0):\n"
    if marker in notice:
        notice = notice.split(marker)[0]
    notice += (
        marker
        + "English Wiktionary contributors: https://en.wiktionary.org/\nText: CC BY-SA 4.0 https://creativecommons.org/licenses/by-sa/4.0/\nExtraction: Kaikki.org / Wiktextract https://kaikki.org/dictionary/rawdata.html\nSnapshot: enwiktionary 2026-10-01; Kaikki extraction 2026-10-21.\nIndividual page, sense, source hash and source labels accompany each imported record.\nSource definitions are reproduced with attribution; automated selection does not imply human review.\nExplicit source script forms are separate records linked by source sense.\nSocial excerpts and article prose remain private and are not redistributed.\n"
    )
    (ROOT / "data/NOTICE.txt").write_text(notice)
    manifest = {
        "schema": 2,
        "version": "0.2.0",
        "title": "Crow Chinese Slang Dictionary",
        "date": TODAY,
        "entries": len(published),
        "headwords": len({r["headword"] for r in published}),
        "senseGroups": len({r["senseGroupId"] for r in published}),
        "sourceImportedSenses": len(
            {
                r["sourceImport"]["selectionInputSha256"]
                for r in published
                if r["entryKind"] == "source-import"
            }
        ),
        "entryKinds": dict(collections.Counter(r["entryKind"] for r in published)),
        "spellingKinds": dict(
            collections.Counter(r["spellingKind"] for r in published)
        ),
        "entriesWithFormRelations": sum(bool(r["formRelations"]) for r in published),
        "sourceAttestedVariantSpellings": len(
            {r["headword"] for r in published if r["spellingKind"] == "script-variant"}
        ),
        "socialUsageEntries": sum(
            any(
                sources[s]["attestationKind"]
                in ["fetched-public-post", "indexed-post-excerpt"]
                for s in r["evidenceIds"]
            )
            for r in published
        ),
        "socialEvidencePages": sum(
            s["attestationKind"] in ["fetched-public-post", "indexed-post-excerpt"]
            for s in sources.values()
        ),
        "evidenceKinds": dict(
            collections.Counter(s["attestationKind"] for s in sources.values())
        ),
        "definitionLanguages": ["en"],
        "regions": dict(
            collections.Counter(r["regionOfAttestation"] for r in published)
        ),
        "registers": dict(
            collections.Counter(t for r in published for t in r["register"])
        ),
        "readingsResolved": sum(bool(r["readings"]) for r in published),
        "previousReleaseEntriesHeld": len(set(base_rows) - set(entries)),
        "heldCandidates": len(held),
        "heldReasons": dict(collections.Counter(r["reason"] for r in held)),
        "sourcePages": len(sources),
        "humanReviewed": 0,
        "completeCoverageClaim": False,
        "license": "CC BY-SA 4.0",
        "artifacts": {
            name: {
                "bytes": (ROOT / "data" / name).stat().st_size,
                "sha256": hashlib.sha256(
                    (ROOT / "data" / name).read_bytes()
                ).hexdigest(),
            }
            for name in [
                "entries.jsonl",
                "entries.jsonl.gz",
                "sources.json",
                "NOTICE.txt",
            ]
        },
    }
    save(ROOT / "data/manifest.json", manifest)
    save(ROOT / "reports/release.json", manifest)
    print(
        canonical(
            {
                k: v
                for k, v in manifest.items()
                if k not in ["artifacts", "regions", "registers", "heldReasons"]
            }
        )
    )


if __name__ == "__main__":
    assemble()
