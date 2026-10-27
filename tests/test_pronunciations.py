import json, tempfile, unittest
from pathlib import Path
from slangdict.pronunciations import export

class PronunciationEvidenceTests(unittest.TestCase):
    def fixture(self, folder):
        root=Path(folder);(root/'data').mkdir();inv=root/'inventory';inv.mkdir()
        row={'id':'a'*24,'headword':'臭棋','spokenVariety':'und','sourceImport':{'sourceFileSha256':'b'*64,'sourceSenseId':'sense-1','sourceUrl':'https://example.org/term','sourceAttribution':'Source contributors'}}
        proof={'entryId':row['id'],'headword':row['headword'],'language':'cmn','tokens':['chou4','qi2'],'lexicalReading':'chòuqí','basis':'exact-primary-source-row','sourceFileSha256':'b'*64,'sourceSenseId':'sense-1','sourceUrl':'https://example.org/term'}
        (root/'data/entries.jsonl').write_text(json.dumps(row)+'\n');(root/'data/manifest.json').write_text('{"artifacts":{}}')
        (inv/'record-readings.jsonl').write_text(json.dumps(proof)+'\n');(inv/'unresolved.jsonl').write_text('')
        return root,inv,row,proof
    def test_reading_does_not_relabel_unknown_lexical_variety_or_include_audio(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,inv,row,proof=self.fixture(tmp);report=export(root,inv)
            result=json.loads((root/'data/pronunciations.jsonl').read_text())
            self.assertEqual(result['lexicalVariety'],'und');self.assertEqual(result['spokenLanguage'],'cmn')
            self.assertFalse(report['audioIncluded']);self.assertFalse(result['humanReviewed'])
            self.assertEqual(json.loads((root/'data/entries.jsonl').read_text()),row)
    def test_unrelated_source_sense_cannot_supply_reading(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,inv,row,proof=self.fixture(tmp);proof['sourceSenseId']='different-sense'
            (inv/'record-readings.jsonl').write_text(json.dumps(proof)+'\n')
            with self.assertRaises(AssertionError):export(root,inv)
    def test_other_variety_cannot_be_assigned_mandarin_reading(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,inv,row,proof=self.fixture(tmp);row['spokenVariety']='hak'
            (root/'data/entries.jsonl').write_text(json.dumps(row)+'\n')
            with self.assertRaises(AssertionError):export(root,inv)
    def test_missing_entry_requires_explicit_unresolved_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,inv,row,proof=self.fixture(tmp);(inv/'record-readings.jsonl').write_text('')
            with self.assertRaises(AssertionError):export(root,inv)
