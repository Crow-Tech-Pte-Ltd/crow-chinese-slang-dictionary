import unittest,tempfile,json
from pathlib import Path
from unittest.mock import patch
from slangdict import full_review
from slangdict.scope import require_scope_approval,digest
class WholeReviewTests(unittest.TestCase):
 def test_chinese_meaning_and_english_novelty_form_are_reviewed_separately(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);(root/'data').mkdir()
   common={'senseGroupId':'shared','definition':'awesome','usageNote':'','spokenVariety':'cmn','community':'Chinese speakers','evidenceIds':['s'],'entryKind':'curated-summary'}
   rows=[{**common,'id':'han','headword':'牛逼'},{**common,'id':'english','headword':'niubility'}]
   (root/'data/entries.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows));(root/'data/sources.json').write_text(json.dumps([{'id':'s','url':'https://example.org/usage','title':'Source','attestationKind':'fetched-page'}]))
   with patch.object(full_review,'ROOT',root):units,data=full_review.build()
   self.assertEqual(len(units),2);self.assertEqual({tuple(u['entryIds']) for u in units},{('han',),('english',)})
 def test_new_or_changed_sense_needs_explicit_scope_approval(self):
  row={'id':'r','headword':'摆烂','definition':'to give up making an effort'}
  with self.assertRaises(ValueError):require_scope_approval([row],{'approvedSenses':{}})
  policy={'approvedSenses':{'r':{'headword':'摆烂','definitionSha256':digest(row['definition'])}}};require_scope_approval([row],policy)
  with self.assertRaises(ValueError):require_scope_approval([{**row,'definition':'a changed sense'}],policy)
if __name__=='__main__':unittest.main()
