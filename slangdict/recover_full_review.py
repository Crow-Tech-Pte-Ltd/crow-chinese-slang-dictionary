"""Recover valid individual decisions from already-paid malformed batch receipts."""
from pathlib import Path
import json,sqlite3,collections
from .full_review import ROOT,SYSTEM,MODELS,save
from .provider import digest,output

def recover():
 work=ROOT/'work/full-review-v070';units={u['id']:u for u in json.loads((work/'units.json').read_text())};inventory=json.loads((work/'inventory.json').read_text());db=sqlite3.connect((ROOT/'work/budget.sqlite').as_uri()+'?mode=ro',uri=True);recovered=0;remaining=[]
 for filename in ['finished-both.json','finished-deepseek.json','finished-glm.json','finished-adjudicator.json']:
  path=work/filename
  if not path.exists():continue
  for error in json.loads(path.read_text()).get('errors',[]):
   role=error['role'];ids=error['unitIds'];phase='full-scope-v070:'+role+':'+digest([inventory['manifestSha256'],ids,digest(SYSTEM)])[:24];refs={f'r{i:02d}':units[uid] for i,uid in enumerate(ids)}
   receipts=db.execute("select path from requests where state='completed' and phase in (?,?) order by created desc",(phase,phase+':retry1')).fetchall()
   for receipt, in receipts:
    response=json.loads(Path(receipt).read_text())
    try:answers=output(response).get('decisions',[])
    except (ValueError,TypeError):continue
    if not isinstance(answers,list):continue
    counts=collections.Counter(a[0] for a in answers if isinstance(a,list) and a and isinstance(a[0],str))
    for answer in answers:
     if not isinstance(answer,list) or len(answer)!=5:continue
     ref,head,decision,category,reason=answer
     if ref not in refs or counts[ref]!=1 or head not in refs[ref]['forms'] or decision not in ['keep','remove','uncertain'] or not isinstance(reason,str) or len(reason)>400:continue
     u=refs[ref];target=work/role/(u['id']+'.json')
     if target.exists():continue
     save(target,{'unitId':u['id'],'headword':u['headword'],'returnedHeadword':head,'forms':u['forms'],'entryIds':u['entryIds'],'decision':decision,'category':category,'reason':reason,'model':MODELS[role],'provider':response.get('provider'),'responseId':response.get('id'),'inputSha256':digest(u),'systemSha256':digest(SYSTEM),'humanReviewed':False,'recoveredFromValidatedPartialReceipt':True});recovered+=1
   remaining.extend({'role':role,'unitId':uid} for uid in ids if not (work/role/(uid+'.json')).exists())
 db.close();report={'recoveredDecisionsWithoutNewRequests':recovered,'remaining':remaining};save(work/'partial-recovery.json',report);print(json.dumps(report));return report
if __name__=='__main__':recover()
