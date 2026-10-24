"""Brute release verification. Raises VerificationError (never assert, so it survives python -O).

No literal study numbers are asserted: every derived artifact is regenerated and compared
byte-for-byte, every sealed artifact is checked against its seal, and the independent
audits are re-run and compared with the committed audit reports.

  python scripts/verify_release.py            # full (re-runs both independent audits, minutes)
  python scripts/verify_release.py --fast     # hashes, seals, freezes, regenerated gates/paired, ledger, manifest
"""
from __future__ import annotations
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check,sha,load,dumps


def _freeze(root,rel):
    lock=load(root/rel)
    for f,digest in lock['sha256_files'].items():check(sha(root/f)==digest,f'{rel}: {f} changed')
    return len(lock['sha256_files'])


def _ledger(root):
    previous='0'*64;receipts=[]
    for line in (root/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines():
        r=json.loads(line);check(r['previous']==previous,'ledger chain broken')
        previous=hashlib.sha256(json.dumps({k:v for k,v in r.items() if k!='receipt_sha256'},sort_keys=True,separators=(',',':')).encode()).hexdigest()
        check(previous==r['receipt_sha256'],'ledger receipt hash');check(sha(root/r['source'])==r['source_sha256'],'ledger source changed: '+r['source'])
        receipts.append(r)
    return receipts


def verify(root=ROOT,fast=False,api_replay=False):
    root=Path(root);out={'schema':'brute.verify-release.v1'}
    rel=load(root/'RELEASE.json');import brute;check(rel['version']==brute.__version__,'RELEASE.json version != brute.__version__')
    # study-001 (BGR v0.90 inheritance), untouched
    out['study001_source_locked']=_freeze(root,'experiments/SOURCE_FREEZE.json')
    st=root/'results/study-001';seal=load(st/'SEAL.json')
    for name,key in (('RESULTS.json','results_sha256'),('SCIENTIFIC.json','scientific_sha256')):check(sha(st/name)==seal[key],'study-001 '+name)
    check(sha(root/'experiments/SOURCE_FREEZE.json')==seal['freeze_sha256'] and sha(root/'experiments/PLAN.json')==seal['plan_sha256'],'study-001 plan/freeze')
    base=root/'baseline/BGR-v0.89.0.zip'
    if base.exists():
        check(sha(base)==load(root/'baseline/IDENTITY.json')['sha256'],'baseline hash')
        with zipfile.ZipFile(base) as z:check(z.testzip() is None,'baseline zip crc')
        out['baseline']='verified'
    else:out['baseline']='absent (optional; excluded from the fork, identity file retained)'
    # study-002
    out['study002_source_locked']=_freeze(root,'experiments/BRUTE_SOURCE_FREEZE_002.json')
    out['release_source_locked']=_freeze(root,'experiments/BRUTE_RELEASE_FREEZE_010.json')
    s2=root/'results/study-002';seal2=load(s2/'SEAL.json')
    for name,key in (('RESULTS.json','results_sha256'),('SCIENTIFIC.json','scientific_sha256'),('CALIBRATION.json','calibration_sha256')):
        check(sha(s2/name)==seal2[key],'study-002 '+name)
    check(sha(root/'experiments/BRUTE_PLAN_002.json')==seal2['plan_sha256'] and sha(root/'experiments/BRUTE_SOURCE_FREEZE_002.json')==seal2['freeze_sha256'],'study-002 plan/freeze')
    from scripts import make_gates,make_paired_analysis
    for mod,name in ((make_gates,'GATES.json'),(make_paired_analysis,'PAIRED_ANALYSIS.json')):
        check((s2/name).read_bytes()==dumps(mod.build()),f'study-002 {name} does not regenerate byte-for-byte')
    check(load(s2/'REPRODUCIBILITY.json')['all_byte_identical'] is True,'study-002 reproducibility record')
    check(sha(s2/'SCIENTIFIC.json')==load(s2/'API_REPLAY.json')['study002_scientific_sha256'],'API replay was made on other results')
    if api_replay:
        from scripts import make_api_replay
        check((s2/'API_REPLAY.json').read_bytes()==dumps(make_api_replay.build()),'API_REPLAY.json does not regenerate')
    if not fast:
        from experiments.independent_audit import audit as audit001
        from experiments.brute_audit import audit as audit002
        check(load(st/'INDEPENDENT_AUDIT.json')==audit001(st),'study-001 fresh audit differs')
        check(load(s2/'INDEPENDENT_AUDIT.json')==audit002(s2),'study-002 fresh audit differs')
        out['independent_audits']='re-run, identical to committed reports'
    js=(root/'ui/data.js').read_text();prefix='window.BGR90_DATA='
    check(js.startswith(prefix) and js.endswith(';\n') and json.loads(js[len(prefix):-2])['source_sha256']==seal['results_sha256'],'ui/data.js')
    receipts=_ledger(root);out['ledger_receipts']=len(receipts)
    sources={r['source'] for r in receipts}
    for need in ('experiments/BRUTE_PLAN_002.json','results/study-002/RESULTS.json','results/study-002/INDEPENDENT_AUDIT.json','results/study-002/GATES.json'):
        check(need in sources,'ledger lacks '+need)
    from scripts.make_manifest import build as manifest
    check((root/'MANIFEST.sha256').read_text()==manifest(root),'MANIFEST.sha256 does not match tracked files')
    out['manifest_files']=len((root/'MANIFEST.sha256').read_text().splitlines())
    g=load(s2/'GATES.json');out['study002_gates_failed']=g['failed'];out['study002_gates_passed']=g['passed']
    out['status']='passed'
    out['validity']='bounded deterministic Moore family with n<=4 hidden states, two actions, two bits; not general intelligence'
    return out


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--fast',action='store_true');ap.add_argument('--api-replay',action='store_true')
    a=ap.parse_args()
    try:print(json.dumps(verify(fast=a.fast,api_replay=a.api_replay),indent=2))
    except VerificationError as e:print('VERIFICATION FAILED:',e);sys.exit(1)
