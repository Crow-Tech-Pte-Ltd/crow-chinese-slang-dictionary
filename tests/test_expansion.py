import unittest, tempfile
from slangdict.provider import Client, ProviderError
from slangdict.social_evidence import social_page_kind
from slangdict.recover_selection import valid_decisions
from slangdict.short_review import resolve_decisions
from slangdict.expand import spelling_forms


class ExpansionTests(unittest.TestCase):
    def test_partial_batch_recovers_only_exact_unambiguous_ids(self):
        good = {"id": "correct", "keep": True, "level": "general-common"}
        typo = {**good, "id": "correcT"}
        duplicate = {**good, "id": "duplicate"}
        valid, held = valid_decisions(
            {"decisions": [good, typo, duplicate, duplicate]},
            {"correct", "missing", "duplicate"},
        )
        self.assertEqual([r["id"] for r in valid], ["correct"])
        self.assertEqual(held, ["duplicate", "missing"])

    def test_short_references_require_exact_spelling(self):
        original = {
            "id": "long-id",
            "headword": "蝦米",
            "definition": "what",
            "sourceTags": ["slang"],
            "sourcePos": "pron",
            "spokenVariety": "nan",
            "regionLabels": ["TW"],
            "sourceAltOf": [],
        }
        refs = {"r00": original}
        bad = {
            "id": "r00",
            "headword": "虾米",
            "keep": True,
            "level": "attested-variant",
        }
        self.assertEqual(resolve_decisions([bad], refs), [])
        good = {**bad, "headword": "蝦米"}
        self.assertEqual(resolve_decisions([good], refs)[0]["id"], "long-id")
        self.assertEqual(resolve_decisions([good, good], refs), [])

    def test_script_forms_do_not_promote_lemma_synonyms(self):
        row = {
            "word": "蝦米",
            "forms": [
                {"form": "虾米", "tags": ["Simplified-Chinese"]},
                {"form": "什麼", "tags": ["alternative"]},
                {"form": "🐮🍺", "tags": ["alternative", "Simplified-Chinese"]},
            ],
        }
        self.assertEqual(
            spelling_forms(row), {"蝦米": "source-headword", "虾米": "script-variant"}
        )

    def test_platform_searches_are_not_post_evidence(self):
        for url in [
            "https://search.bilibili.com/all?keyword=test",
            "https://www.douyin.com/search/test",
            "https://www.douyin.com/shipin/123",
            "https://www.zhihu.com/topic/123",
            "https://weibo.com/u/123456",
            "https://www.xiaohongshu.com/user/profile/123",
            "https://www.1point3acres.com/bbs/forum.php?mod=forumdisplay&fid=2",
        ]:
            self.assertEqual(social_page_kind(url), "platform-index", url)
        for url in [
            "https://www.bilibili.com/video/BV1ZW4y1r7K3/",
            "https://m.weibo.cn/detail/123456",
            "https://www.zhihu.com/question/123/answer/456",
            "https://www.dcard.tw/f/talk/p/123456",
            "https://www.ptt.cc/bbs/Gossiping/M.123456.A.123.html",
            "https://www.1point3acres.com/bbs/forum.php?mod=viewthread&tid=123",
        ]:
            self.assertEqual(social_page_kind(url), "public-post", url)

    def test_authorized_cap_raise_keeps_ledger_usage(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = Client(tmp, "unused", 2)
            with first.connect() as db:
                db.execute("UPDATE budget SET spent=12345,calls=8 WHERE id=1")
                db.commit()
            raised = Client(tmp, "unused", 8, raise_cap=True)
            self.assertEqual(raised.summary()["spentOrReservedUsd"], 0.012345)
            self.assertEqual(raised.summary()["calls"], 8)
            with self.assertRaises(ProviderError):
                Client(tmp, "unused", 2, raise_cap=True)


if __name__ == "__main__":
    unittest.main()
