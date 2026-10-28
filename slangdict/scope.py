"""Keep the collection about Chinese slang rather than general jargon.

Decisions are sense-specific and definition-bound. Non-Hanzi spelling alone is
never an exclusion reason. No model calls, source scraping or audio changes.
"""
from pathlib import Path
import argparse, collections, copy, datetime, gzip, hashlib, json, re
ROOT=Path(__file__).resolve().parents[1]
def digest(text):return hashlib.sha256(text.encode()).hexdigest()
def compact(value):return json.dumps(value,ensure_ascii=False,separators=(',',':')).encode()
def load_policy(root=ROOT):return json.loads((Path(root)/'config/slang-scope.json').read_text())
def exclusion(row,policy):
    for decision in policy['exclusions']:
        if row['id']!=decision['entryId']:continue
        if row['headword']!=decision['headword'] or digest(row['definition'])!=decision['definitionSha256']:
            raise ValueError('Scope decision needs re-review after a sense change: '+row['id'])
        return decision
    word=row['headword'].casefold()
    if word in policy['genericEnglishTechnicalWords'] and re.search(policy['genericTechnicalDefinitionPattern'],row['definition']):
        return {'entryId':row['id'],'headword':row['headword'],'definitionSha256':digest(row['definition']),'category':'ordinary-technical-vocabulary','reason':'Ordinary English technical sense, without a Chinese slang meaning.'}
    for preserved in policy.get('preservedSenseExceptions',[]):
        if row['id']==preserved['entryId']:
            if row['headword']!=preserved['headword'] or digest(row['definition'])!=preserved['definitionSha256']:
                raise ValueError('Preserved slang sense needs re-review after a change: '+row['id'])
            return None
    if word in {r['headword'].casefold() for r in policy['exclusions']}:
        return {'entryId':row['id'],'headword':row['headword'],'definitionSha256':digest(row['definition']),'category':'scope-review-required','reason':'This previously over-broad word requires an explicit Chinese slang sense review before reuse.'}
    return None

def intake_instruction():
    return " Scope is Chinese slang, not a general internet or terminology dictionary. Do not accept ordinary technical operations (rooting, routers, storage units), institutional/workplace labels or literal foreign borrowings solely because Chinese speakers use them. Generic English slang with its ordinary English meaning, and Chinese-media reporting of English youth slang, do not establish a Chinese slang sense. Keep Chinese-origin abbreviations (YYDS, XSWL), established Chinese informal/idiomatic expressions and Chinese-specific semantic shifts (including slang senses of QQ, M and SL). Evaluate the particular sense; non-Hanzi spelling alone is never a rejection reason."

def screen(rows,policy):
    accepted=[];held=[]
    for row in rows:
        reason=exclusion(row,policy)
        if reason:held.append(reason)
        else:accepted.append(copy.deepcopy(row))
    accepted_ids={r['id'] for r in accepted}
    for row in accepted:
        if 'formRelations' in row:row['formRelations']=[x for x in row['formRelations'] if x['targetId'] in accepted_ids]
    return accepted,held

def restrict_sources(rows,sources):
    ids={s for r in rows for s in r['evidenceIds']}
    return {sid:source for sid,source in sources.items() if sid in ids}

def atomic(path,body):
    path=Path(path);temp=path.with_suffix(path.suffix+'.pending');temp.write_bytes(body);temp.replace(path)

def clean_release(root=ROOT,version='0.6.0',release_date='2026-10-29'):
    datetime.date.fromisoformat(release_date)
    root=Path(root);data=root/'data';policy=load_policy(root);manifest=json.loads((data/'manifest.json').read_text())
    original=[json.loads(l) for l in (data/'entries.jsonl').read_text().splitlines() if l]
    accepted,held=screen(original,policy)
    archive=root/'work/scope-archive-2026-10-29.jsonl'
    if held and not archive.exists():
        archive.parent.mkdir(exist_ok=True);bad={h['entryId'] for h in held};atomic(archive,b''.join(compact(r)+b'\n' for r in original if r['id'] in bad))
    exclusions_path=data/'scope-exclusions.jsonl'
    previous=[json.loads(l) for l in exclusions_path.read_text().splitlines()] if exclusions_path.exists() else []
    decisions={d['entryId']:d for d in previous+held};assert not set(decisions)&{r['id'] for r in accepted}
    held=sorted(decisions.values(),key=lambda r:r['entryId']);ids={r['id'] for r in accepted}
    sources=restrict_sources(accepted,{r['id']:r for r in json.loads((data/'sources.json').read_text())})
    body=b''.join(compact(r)+b'\n' for r in sorted(accepted,key=lambda r:r['id']))
    atomic(data/'entries.jsonl',body);atomic(data/'entries.jsonl.gz',gzip.compress(body,mtime=0))
    atomic(data/'sources.json',json.dumps(sorted(sources.values(),key=lambda r:r['id']),ensure_ascii=False,indent=2).encode()+b'\n')
    atomic(exclusions_path,b''.join(compact(r)+b'\n' for r in held))
    for name in ['pronunciations.jsonl','pronunciation-unresolved.jsonl']:
        path=data/name
        if path.exists():
            rows=[json.loads(l) for l in path.read_text().splitlines() if l];rows=[r for r in rows if r['entryId'] in ids]
            body=b''.join(compact(r)+b'\n' for r in rows);atomic(path,body);atomic(data/(name+'.gz'),gzip.compress(body,mtime=0))
    notice=data/'NOTICE.txt';text=notice.read_text();text=text.replace(text.splitlines()[0],'Crow Chinese Slang Dictionary, v'+version,1)
    if 'Scope correction (2026-10-29)' not in text:
        text+='\nScope correction (2026-10-29)\nGeneric technical terms, ordinary vocabulary and unrelated English slang are excluded from the accepted collection. Decisions and reasons: scope-exclusions.jsonl; reproducible rules: ../config/slang-scope.json. Genuine Chinese abbreviations, semantic shifts and regional slang are retained.\n'
    atomic(notice,text.encode())
    rows=accepted
    manifest.update(version=version,date=release_date,entries=len(rows),headwords=len({r['headword'] for r in rows}),senseGroups=len({r['senseGroupId'] for r in rows}),sourceImportedSenses=len({r['sourceImport']['selectionInputSha256'] for r in rows if r['entryKind']=='source-import'}),entryKinds=dict(collections.Counter(r['entryKind'] for r in rows)),spellingKinds=dict(collections.Counter(r['spellingKind'] for r in rows)),entriesWithFormRelations=sum(bool(r['formRelations']) for r in rows),sourceAttestedVariantSpellings=len({r['headword'] for r in rows if r['spellingKind']=='script-variant'}),socialUsageEntries=sum(any(sources[s]['attestationKind'] in ['fetched-public-post','indexed-post-excerpt'] for s in r['evidenceIds']) for r in rows),socialEvidencePages=sum(s['attestationKind'] in ['fetched-public-post','indexed-post-excerpt'] for s in sources.values()),evidenceKinds=dict(collections.Counter(s['attestationKind'] for s in sources.values())),regions=dict(collections.Counter(r['regionOfAttestation'] for r in rows)),registers=dict(collections.Counter(t for r in rows for t in r['register'])),readingsResolved=sum(bool(r['readings']) for r in rows),sourcePages=len(sources))
    readings=[json.loads(l) for l in (data/'pronunciations.jsonl').read_text().splitlines()];unresolved=[json.loads(l) for l in (data/'pronunciation-unresolved.jsonl').read_text().splitlines()]
    assert {r['entryId'] for r in readings}|{r['entryId'] for r in unresolved}==ids
    manifest['pronunciationEvidence'].update(resolvedRecords=len(readings),unresolvedOrUnsupportedRecords=len(unresolved),resolvedByLanguage=dict(collections.Counter(r['spokenLanguage'] for r in readings)),evidenceBasis=dict(collections.Counter(r['basis'] for r in readings)))
    manifest['heldReasons']={k:v for k,v in manifest.get('heldReasons',{}).items() if not k.startswith('scope/')}
    for decision in held:manifest['heldReasons'].pop(decision['reason'],None)
    manifest['heldReasons'].update({'scope/'+k:v for k,v in collections.Counter(r['category'] for r in held).items()})
    manifest['heldCandidates']=sum(manifest['heldReasons'].values())
    manifest['previousReleaseEntriesHeld']=len(held)
    manifest['scopeReview']={'recordsScreened':len(rows)+len(held),'excludedRecords':len(held),'excludedByCategory':dict(collections.Counter(r['category'] for r in held)),'exclusions':'scope-exclusions.jsonl','policySha256':hashlib.sha256((root/'config/slang-scope.json').read_bytes()).hexdigest(),'notAScriptFilter':True,'completeHumanReview':False}
    manifest['artifacts']['scope-exclusions.jsonl']={}
    for name in manifest['artifacts']:
        b=(data/name).read_bytes();manifest['artifacts'][name]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
    atomic(data/'manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2).encode()+b'\n')
    atomic(root/'reports/release.json',json.dumps(manifest,ensure_ascii=False,indent=2).encode()+b'\n')
    return {'acceptedRecords':len(rows),'distinctSpellings':manifest['headwords'],'excludedRecords':len(held),'byCategory':manifest['scopeReview']['excludedByCategory'],'pronunciationEvidence':manifest['pronunciationEvidence']}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--version',default='0.6.0');p.add_argument('--date',default='2026-10-29');a=p.parse_args();print(json.dumps(clean_release(a.root,a.version,a.date),ensure_ascii=False,indent=2))
