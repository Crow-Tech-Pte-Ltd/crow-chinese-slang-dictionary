import json,unittest,copy,hashlib
from pathlib import Path
from slangdict.scope import load_policy,screen,exclusion
ROOT=Path(__file__).resolve().parents[1]
class ScopeTests(unittest.TestCase):
 def setUp(self):self.policy=load_policy(ROOT)
 def test_ordinary_root_is_rejected_even_with_a_new_entry_id(self):
  row={'id':'new-root-sense','headword':'root','definition':'to root an Android device and obtain privileged access'}
  self.assertEqual(exclusion(row,self.policy)['category'],'ordinary-technical-vocabulary')
 def test_known_english_jargon_needs_review_even_under_a_new_id(self):
  row={'id':'future-bruh-id','headword':'bruh','definition':'A generic English address term'}
  self.assertIsNotNone(exclusion(row,self.policy))
 def test_rule_is_not_a_hanzi_or_latin_filter(self):
  for word,definition in [('YYDS','Abbreviation of 永远的神'),('XSWL','Abbreviation of 笑死我了'),('屎山','A pejorative metaphor for unmaintainable code')]:
   self.assertIsNone(exclusion({'id':'new-'+word,'headword':word,'definition':definition},self.policy))
 def test_changed_definition_requires_a_new_scope_decision(self):
  r=self.policy['exclusions'][0]
  with self.assertRaises(ValueError):exclusion({'id':r['entryId'],'headword':r['headword'],'definition':'A revised sense'},self.policy)
 def test_removed_relations_do_not_dangle_and_original_input_is_preserved(self):
  bad=self.policy['exclusions'][0];definition='fixture';policy={**self.policy,'exclusions':[{**bad,'definitionSha256':hashlib.sha256(definition.encode()).hexdigest()}]}
  row={'id':bad['entryId'],'headword':bad['headword'],'definition':definition};good={'id':'keep','headword':'牛逼','definition':'awesome','formRelations':[{'targetId':bad['entryId']} ]};original=copy.deepcopy(good)
  kept,held=screen([row,good],policy);self.assertEqual(kept[0]['formRelations'],[]);self.assertEqual(good,original);self.assertEqual(len(held),1)
 def test_release_keeps_slang_senses_of_ambiguous_spellings(self):
  rows=[json.loads(l) for l in (ROOT/'data/entries.jsonl').read_text().splitlines()]
  byword={word:[r for r in rows if r['headword']==word] for word in ['QQ','M','SL','seed','op','YYDS','XSWL']}
  self.assertTrue(any('weeping' in r['definition'] for r in byword['QQ']))
  self.assertFalse(any('Tencent QQ' in r['definition'] for r in byword['QQ']))
  self.assertTrue(any('menstru' in r['definition'] for r in byword['M']))
  self.assertFalse(any('megabyte' in r['definition'] for r in byword['M']))
  self.assertTrue(any('savescum' in r['definition'] for r in byword['SL']))
  self.assertTrue(any('serial number' in r['definition'] for r in byword['seed']))
  self.assertTrue(all(byword[w] for w in ['YYDS','XSWL']))
  self.assertEqual(len(rows),7455);self.assertFalse(any(r['headword'].casefold() in ['propoorty','niubility','democrazy','ddl'] for r in rows));self.assertFalse(any(r['headword']=='root' for r in rows))
if __name__=='__main__':unittest.main()
