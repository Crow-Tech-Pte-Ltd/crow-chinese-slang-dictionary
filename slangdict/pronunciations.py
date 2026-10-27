"""Export source-bound pronunciation evidence separately from lexical variety labels.

Usage: python3 -m slangdict.pronunciations --inventory /path/to/private/audio-inventory
No audio, credentials, or private filesystem locations enter the public dataset.
"""
from pathlib import Path
import argparse, collections, gzip, hashlib, json, re

def write(path,body):
    tmp=path.with_suffix(path.suffix+'.pending');tmp.write_bytes(body);tmp.replace(path)

def export(root, inventory):
    root,inventory=Path(root),Path(inventory)
    entries={e['id']:e for e in map(json.loads,(root/'data/entries.jsonl').read_text().splitlines())}
    readings=[];seen=set()
    for line in (inventory/'record-readings.jsonl').read_text().splitlines():
        proof=json.loads(line);entry=entries[proof['entryId']]
        assert entry['headword']==proof['headword']
        assert proof['entryId'] not in seen;seen.add(proof['entryId'])
        lang=proof['language'];assert lang in ['cmn','yue']
        assert entry['spokenVariety'] in ['und',lang], entry['headword']
        tokens=proof['tokens'];pattern=r'[a-züv:]+[1-5]' if lang=='cmn' else r'[a-z]+[1-6]'
        assert tokens and all(re.fullmatch(pattern,t) for t in tokens)
        basis=proof['basis']
        if basis=='exact-primary-source-row':
            original=entry['sourceImport']
            assert proof['sourceFileSha256']==original['sourceFileSha256']
            assert proof['sourceSenseId']==original['sourceSenseId']
            assert proof['sourceUrl']==original['sourceUrl']
            evidence=[{'sourceId':'en-wiktionary-kaikki-20261021','sourceUrl':proof['sourceUrl'],'sourceLicense':'CC BY-SA 4.0','sourceAttribution':original['sourceAttribution'],'sourceFileSha256':proof['sourceFileSha256'],'sourceSenseId':proof['sourceSenseId']}]
        else:
            assert basis=='unique-compatible-whole-word-dictionary-reading'
            evidence=[]
            for e in proof.get('dictionaryEvidence',[]):
                assert e['tokens']==tokens and e['language']==lang
                assert e['sourceLicense'] in ['CC BY-SA 4.0','CC BY-SA 3.0','MIT']
                assert e['sourceId'] and e['sourceAttribution'] and e['sourceUrl'].startswith('https://')
                evidence.append({k:e[k] for k in ['sourceId','sourceUrl','sourceLicense','sourceAttribution']})
            assert evidence
        readings.append({'entryId':entry['id'],'headword':entry['headword'],'spokenLanguage':lang,'lexicalVariety':entry['spokenVariety'],'system':'pinyin' if lang=='cmn' else 'jyutping','lexicalReading':proof['lexicalReading'],'normalizedSyllables':tokens,'basis':basis,'evidence':evidence,'humanReviewed':False,'scope':'Source-bound whole-word reading. Does not establish a local accent, certify every slang sense, or verify generated audio.'})
    unresolved=[]
    for line in (inventory/'unresolved.jsonl').read_text().splitlines():
        j=json.loads(line);e=entries[j['entryId']]
        assert e['headword']==j['headword'] and e['id'] not in seen;seen.add(e['id'])
        unresolved.append({k:j[k] for k in ['entryId','headword','spokenVariety','reason','sourceReadings'] if k in j})
    assert seen==set(entries),'Every spelling/sense must be accounted for'
    data=root/'data';artifacts={}
    for name,rows in [('pronunciations.jsonl',readings),('pronunciation-unresolved.jsonl',unresolved)]:
        body=''.join(json.dumps(j,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n' for j in sorted(rows,key=lambda x:x['entryId'])).encode()
        for filename,content in [(name,body),(name+'.gz',gzip.compress(body,mtime=0))]:
            write(data/filename,content);artifacts[filename]={'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()}
    report={'resolvedRecords':len(readings),'unresolvedOrUnsupportedRecords':len(unresolved),'resolvedByLanguage':dict(collections.Counter(j['spokenLanguage'] for j in readings)),'evidenceBasis':dict(collections.Counter(j['basis'] for j in readings)),'readingsAreSeparateFromLexicalVariety':True,'humanReviewed':0,'audioIncluded':False,'completeCoverageClaim':False}
    manifest=json.loads((data/'manifest.json').read_text());manifest['artifacts'].update(artifacts);manifest['pronunciationEvidence']=report
    write(data/'manifest.json',(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode())
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument('--inventory',type=Path,required=True);p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args();print(json.dumps(export(a.root,a.inventory),indent=2))
if __name__=='__main__':main()
