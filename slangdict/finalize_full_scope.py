"""Finalize the frozen full-corpus audit with explicit product-scope exclusions."""
from pathlib import Path
import json,hashlib,gzip,collections,argparse
from slangdict.full_review import ROOT,MODELS,SYSTEM,save
from slangdict.provider import digest
from slangdict.scope import clean_release,atomic,compact

def main(apply=False):
 work=ROOT/'work/full-review-v070';units=json.loads((work/'units.json').read_text());inventory=json.loads((work/'inventory.json').read_text());rows=[json.loads(l) for l in (ROOT/'data/entries.jsonl').read_text().splitlines()];byid={r['id']:r for r in rows}
 assert inventory['records']==8735 and inventory['units']==len(units)==6218
 assert hashlib.sha256((ROOT/'data/manifest.json').read_bytes()).hexdigest()==inventory['manifestSha256'],'Audit input changed'
 reviews={r:{p.stem:json.loads(p.read_text()) for p in (work/r).glob('*.json')} for r in MODELS}
 # These specific meanings remain ordinary terminology even if called Internet slang
 # by an upstream source. Chinese-specific metaphorical meanings remain separate.
 ordinary_units=set('00478e71f8263306 01f3d2e7a956da7b 0a37b83f63191b71 0fb7392582b7c185 0fe3ac06b419b0d7 1064b8e54dc01e54 187e6f5878ce1a50 19e2d74caf363baf 1fcb46473fc516e5 24ee30fe0044188c 32664f74486d964c 3661f7c83ae5ae86 4ec7f9f5a2abdaef 50346c39ad1867f4 538255b7bc2141d4 54232e3651e0aa5e 572dc697a298fcf6 5c422adc517b43d9 72dd8cbdf290de34 798306ec86f7a126 7d323b9390e65cdd 870ad24d089651fc 8d3954a430f79f84 99a90d599f7a74e7 b43f758d39eeefca d10e5b1a426987bf d63e621bfadf00e8 f4530fe3c8e2682a'.split())
 foreign_heads={s.casefold() for s in ['propoorty','Democrazy','Togayther','antizen','ballache','eggache','niubility','shitizen','suihide','vegeteal','Newspaper Eat','FuGuo','MeiDi','Fam J','DDL','OT','Tapau','cm','fol','fo','repo','sd','bam','port','cos','coser','OIer','push','pish','homo','(', '( )', '《 》','。。。','□']}
 audit=[];kept=[];held=[];third=0;overrides=0
 for u in units:
  rs=[]
  for role in ['deepseek','glm']:
   r=reviews[role][u['id']];assert r['inputSha256']==digest(u) and r['systemSha256']==digest(SYSTEM) and r['model']==MODELS[role];rs.append(r)
  if not all(r['decision']=='keep' for r in rs):
   r=reviews['adjudicator'][u['id']];assert r['inputSha256']==digest(u) and r['systemSha256']==digest(SYSTEM) and r['model']==MODELS['adjudicator'];rs.append(r);third+=1
  counts=collections.Counter(r['decision'] for r in rs)
  verdict='keep' if counts['keep']>=2 else ('remove' if counts['remove']>=2 else 'hold')
  reason='At least two independent scope checks support Chinese slang inclusion.' if verdict=='keep' else ('At least two independent scope checks reject this meaning or form.' if verdict=='remove' else 'Scope remains uncertain; excluded pending better usage evidence.')
  category=next((r['category'] for r in rs if r['decision']==('remove' if verdict=='remove' else 'uncertain')),rs[0]['category'])
  override=None
  if set(u['forms']) and (any(h.casefold() in foreign_heads for h in u['forms']) or u['id'] in ordinary_units):
   override={'category':'ordinary-terminology' if u['id'] in ordinary_units else 'generic-foreign-or-novelty','reason':'Ordinary internet terminology without a distinct Chinese slang meaning.' if u['id'] in ordinary_units else 'English novelty, generic jargon, or learner transcription; outside this collection.'}
  d=u['definitions'][0].lower()
  if (u['headword']=='安全佬' and 'safety officer' in d) or (u['headword']=='120' and 'ambulance' in d) or (u['headword']=='flag' and d.endswith('flag')):override={'category':'ordinary-terminology','reason':'Neutral occupational label, emergency number, or circular reference; no useful slang sense.'}
  if (u['headword']=='PK' and 'player killing' in d) or (u['headword']=='SM' and 's&m' in d) or (u['headword']=='V' and 'virtual youtuber' in d) or (u['headword']=='GV' and 'gay porn' in d):override={'category':'generic-foreign','reason':'Ordinary foreign abbreviation; this supplied sense has no Chinese-specific slang shift.'}
  if override:verdict='remove';category=override['category'];reason=override['reason'];overrides+=1
  entry_proofs=[{'entryId':i,'headword':byid[i]['headword'],'definitionSha256':hashlib.sha256(byid[i]['definition'].encode()).hexdigest()} for i in u['entryIds']]
  item={'unitId':u['id'],'forms':u['forms'],'senses':entry_proofs,'decision':verdict,'category':category,'reason':reason,'reviewers':[{k:r.get(k) for k in ['model','provider','responseId','decision','category','reason','inputSha256','systemSha256','humanReviewed']} for r in rs],'productScopeOverride':override,'humanReviewed':False}
  audit.append(item)
  (kept if verdict=='keep' else held).extend(entry_proofs)
 summary={'inputRecords':len(rows),'reviewUnits':len(units),'primaryDecisionsPerModel':{role:len(reviews[role]) for role in ['deepseek','glm']},'thirdChecks':third,'explicitProductScopeDecisions':overrides,'acceptedRecords':len(kept),'removedOrHeldRecords':len(held),'decisionsByUnit':dict(collections.Counter(a['decision'] for a in audit)),'byCategory':dict(collections.Counter(a['category'] for a in audit if a['decision']!='keep')),'humanReviewed':False}
 save(work/'aggregate-preview.json',summary);save(work/'aggregate-private.json',audit);print(json.dumps(summary,indent=2))
 if not apply:return
 policy=json.loads((ROOT/'config/slang-scope.json').read_text());policy['approvedSenses']={p['entryId']:{'headword':p['headword'],'definitionSha256':p['definitionSha256'],'review':'full-scope-v0.7.0'} for p in kept}
 for a in audit:
  if a['decision']!='keep':
   for proof in a['senses']:policy['exclusions'].append({**proof,'category':a['category'],'reason':'Full scope review: '+a['reason'],'reviewUnitId':a['unitId'],'humanReviewed':False})
 excluded_heads={p['headword'].casefold() for p in policy['exclusions']}
 policy['preservedSenseExceptions']=[{**p,'reason':'Distinct retained Chinese slang sense reviewed in v0.7.0.'} for p in kept if p['headword'].casefold() in excluded_heads]
 policy['fullReview']={'version':'0.7.0','inputManifestSha256':inventory['manifestSha256'],'rule':'Two keep votes required; uncertain or rejected senses stay out. Explicit product-scope exclusions override inclusion.','humanReviewed':False}
 atomic(ROOT/'config/slang-scope.json',json.dumps(policy,ensure_ascii=False,indent=2).encode()+b'\n')
 body=b''.join(compact(a)+b'\n' for a in audit);atomic(ROOT/'data/full-scope-review.jsonl',body);atomic(ROOT/'data/full-scope-review.jsonl.gz',gzip.compress(body,mtime=0))
 m=json.loads((ROOT/'data/manifest.json').read_text());m['fullScopeReview']={**summary,'inputVersion':'0.6.0','inputManifestSha256':inventory['manifestSha256'],'decisions':'full-scope-review.jsonl','models':MODELS,'definitionsRewritten':False,'pronunciationsRegenerated':False,'rule':policy['fullReview']['rule']}
 for name in ['full-scope-review.jsonl','full-scope-review.jsonl.gz']:m['artifacts'][name]={}
 atomic(ROOT/'data/manifest.json',json.dumps(m,ensure_ascii=False,indent=2).encode()+b'\n')
 print(json.dumps(clean_release(ROOT,'0.7.0','2026-10-29'),ensure_ascii=False,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');a=p.parse_args();main(a.apply)
