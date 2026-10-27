import unittest, tempfile, json
from unittest.mock import patch
from slangdict.provider import Client, ProviderError, output
from slangdict.pipeline import contexts, safe_url, valid_candidate, disallowed_source


class Reply:
    def __init__(self, data):
        self.data = data

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read(self, n):
        return json.dumps(self.data).encode()


class Opener:
    def __init__(self, data=None, error=None):
        self.data = data
        self.error = error
        self.calls = 0

    def open(self, *args, **kwargs):
        self.calls += 1
        if self.error:
            raise self.error
        return Reply(self.data)


class PipelineTests(unittest.TestCase):
    def response(self):
        return {
            "model": "deepseek/test",
            "usage": {"cost": 0.001},
            "choices": [
                {"finish_reason": "stop", "message": {"content": '{"entries":[]}'}}
            ],
        }

    def test_completed_paid_call_is_not_repeated(self):
        with tempfile.TemporaryDirectory() as tmp:
            client = Client(tmp, "unused", 2)
            opener = Opener(self.response())
            with (
                patch("slangdict.provider.read_key", return_value="test-placeholder"),
                patch(
                    "slangdict.provider.urllib.request.build_opener",
                    return_value=opener,
                ),
            ):
                a = client.call(
                    "test", "deepseek/test", "system", {"term": "吃蛇"}, web=True
                )
                b = client.call(
                    "test", "deepseek/test", "system", {"term": "吃蛇"}, web=True
                )
            self.assertEqual(a, b)
            self.assertEqual(opener.calls, 1)
            self.assertEqual(client.summary()["calls"], 1)
            self.assertAlmostEqual(client.summary()["spentOrReservedUsd"], 0.008)

    def test_unknown_charge_does_not_retry_or_refund(self):
        with tempfile.TemporaryDirectory() as tmp:
            client = Client(tmp, "unused", 2)
            opener = Opener(error=TimeoutError())
            with (
                patch("slangdict.provider.read_key", return_value="test-placeholder"),
                patch(
                    "slangdict.provider.urllib.request.build_opener",
                    return_value=opener,
                ),
            ):
                for _ in range(2):
                    with self.assertRaises(ProviderError):
                        client.call("test", "deepseek/test", "system", {"term": "吃蛇"})
            self.assertEqual(opener.calls, 1)
            self.assertGreater(client.summary()["spentOrReservedUsd"], 0)
            self.assertEqual(client.summary()["states"], {"unknown-charge": 1})

    def test_failed_outputs_are_not_accepted(self):
        r = self.response()
        r["choices"][0]["finish_reason"] = "length"
        with self.assertRaises(ValueError):
            output(r)

    def test_budget_cap_persists_across_restarts(self):
        with tempfile.TemporaryDirectory() as tmp:
            Client(tmp, "unused", 0.1)
            with self.assertRaises(ProviderError):
                Client(tmp, "unused", 2)

    def test_model_identity_mismatch_is_quarantined(self):
        with tempfile.TemporaryDirectory() as tmp:
            client = Client(tmp, "unused", 2)
            r = self.response()
            r["model"] = "other/model"
            opener = Opener(r)
            with (
                patch("slangdict.provider.read_key", return_value="test-placeholder"),
                patch(
                    "slangdict.provider.urllib.request.build_opener",
                    return_value=opener,
                ),
            ):
                with self.assertRaises(ProviderError):
                    client.call("test", "deepseek/test", "system", {})
            self.assertEqual(client.summary()["states"], {"unknown-charge": 1})

    def test_unattested_words_cannot_gain_context(self):
        self.assertEqual(contexts("本地人用吃蛇来形容偷懒。", "不存在词"), "")
        self.assertIn("偷懒", contexts("本地人用吃蛇来形容偷懒。", "吃蛇"))

    def test_private_network_sources_are_refused(self):
        self.assertFalse(safe_url("http://127.0.0.1/private"))
        self.assertFalse(safe_url("https://localhost/foo"))
        self.assertFalse(safe_url("https://user:password@example.com/"))

    def test_generated_and_nd_material_is_not_primary_usage_evidence(self):
        self.assertTrue(disallowed_source("https://hanzidesk.com/dictionary/test"))
        self.assertTrue(
            disallowed_source(
                "https://github.com/Crow-Tech-Pte-Ltd/crow-chinese-dictionary"
            )
        )
        self.assertTrue(disallowed_source("https://dict.revised.moe.edu.tw/search"))
        self.assertFalse(disallowed_source("https://www.abc.net.au/news/example"))

    def test_unknown_pronunciation_is_not_filled_by_model_fields(self):
        row = {
            "headword": "母湯",
            "senseKey": "do-not",
            "definition": "Do not; an informal warning.",
            "usageNote": "Taiwanese Hokkien-influenced writing.",
            "spokenVariety": "nan",
            "register": ["informal"],
            "sourceUrls": ["https://example.com/a"],
            "commonalityReason": "Documented usage",
        }
        self.assertTrue(valid_candidate(row))
        row["spokenVariety"] = "invented-dialect"
        self.assertFalse(valid_candidate(row))
        row["spokenVariety"] = "nan"
        row["definition"] = "<script>bad</script>"
        self.assertFalse(valid_candidate(row))


if __name__ == "__main__":
    unittest.main()
