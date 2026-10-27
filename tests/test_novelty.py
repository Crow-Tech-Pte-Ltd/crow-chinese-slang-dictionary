import json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from slangdict import novelty
from slangdict.pipeline import write_rows, read_rows


class FakeClient:
    def __init__(self):
        self.calls = 0

    def call(self, *args, **kwargs):
        self.calls += 1
        items = args[3]["items"]
        decisions = []
        for item in items:
            definition = item["candidate"]["definition"]
            decisions.append(
                {
                    "ref": item["ref"],
                    "headword": item["candidate"]["headword"],
                    "decision": "new-meaning"
                    if definition == "a genuinely different sense"
                    else "already-described",
                    "matchRef": None
                    if definition == "a genuinely different sense"
                    else "k00",
                    "reason": "test fixture",
                }
            )
        return {
            "id": "fake-response",
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {"content": json.dumps({"decisions": decisions})},
                }
            ],
        }


class NoveltyTests(unittest.TestCase):
    def test_new_region_alone_is_not_a_new_sense_and_resume_reuses_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "work").mkdir()
            (root / "work/v0.2-base").mkdir()
            base = {
                "id": "published",
                "headword": "好家伙",
                "definition": "an interjection of surprise",
                "usageNote": "",
                "spokenVariety": "cmn",
            }
            write_rows(root / "work/v0.2-base/entries.jsonl", [base])

            def candidate(uid, word, definition):
                return {
                    "id": uid,
                    "headword": word,
                    "definition": definition,
                    "usageNote": "",
                    "spokenVariety": "cmn",
                    "regionId": "another-region",
                }

            rows = [
                candidate("same", "好家伙", "an interjection of surprise"),
                candidate("new-sense", "好家伙", "a genuinely different sense"),
                candidate("new-word", "新词测试", "a test fixture"),
            ]
            write_rows(root / "work/candidates.jsonl", rows)
            client = FakeClient()
            with patch.object(novelty, "ROOT", root):
                novelty.run(client)
                first = {r["id"]: r for r in read_rows(root / "work/candidates.jsonl")}
                self.assertFalse(novelty.allowed(first["same"]))
                self.assertTrue(novelty.allowed(first["new-sense"]))
                self.assertEqual(
                    first["new-word"]["coverageGate"]["decision"], "new-spelling"
                )
                novelty.run(client)
            self.assertEqual(client.calls, 1)
            self.assertFalse(
                novelty.allowed({"coverageGate": {"decision": "uncertain"}})
            )
            self.assertTrue(novelty.allowed({}))
            self.assertFalse(
                novelty.allowed(
                    {
                        "coverageGate": {"decision": "new-spelling"},
                        "scopeAudit": {"approved": False},
                    }
                )
            )
            self.assertFalse(novelty.allowed({"researchKind": "gap-targeted"}))


if __name__ == "__main__":
    unittest.main()
