import unittest
from pathlib import Path
from slangdict.validate import validate

ROOT = Path(__file__).resolve().parents[1]


class ReleaseTests(unittest.TestCase):
    @unittest.skipUnless(
        (ROOT / "data/manifest.json").exists(), "No built release in this checkout"
    )
    def test_release_provenance_and_checksums(self):
        proof = validate(ROOT)
        self.assertGreater(proof["entriesValidated"], 0)
        self.assertTrue(proof["privatePageTextAbsent"])


if __name__ == "__main__":
    unittest.main()
