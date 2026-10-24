"""Strict release byte hashes, independent reconstruction and scientific gates."""
from pathlib import Path
import hashlib,json,zipfile
from experiments.independent_audit import audit
ROOT=Path(__file__).resolve().parents[1]

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        while True:
            b=f.read(1<<20)
            if not b:break
            h.update(b)
    return h.hexdigest()


def listed():
    return {p.relative_to(ROOT).as_posix():p for p in ROOT.rglob('*') if p.is_file()
      and p.name!='MANIFEST.sha256' and not p.name.endswith('.pyc')
      and not any(s in ('__pycache__','.pytest_cache','runs','.git') for s in p.relative_to(ROOT).parts)}


def verify():
    lock=json.loads((ROOT/'experiments/SOURCE_FREEZE.json').read_text())
    for rel,expected in lock['sha256_files'].items():assert sha(ROOT/rel)==expected,rel
    baseline=ROOT/'baseline/BGR-v0.89.0.zip'
    identity=json.loads((ROOT/'baseline/IDENTITY.json').read_text())
    assert sha(baseline)==identity['sha256']
    with zipfile.ZipFile(baseline) as z:assert z.testzip() is None
    st=ROOT/'results/study-001'
    seal=json.loads((st/'SEAL.json').read_text())
    assert sha(st/'RESULTS.json')==seal['results_sha256']
    assert sha(st/'SCIENTIFIC.json')==seal['scientific_sha256']
    assert sha(ROOT/'experiments/SOURCE_FREEZE.json')==seal['freeze_sha256']
    assert sha(ROOT/'experiments/PLAN.json')==seal['plan_sha256']
    original=json.loads((st/'INDEPENDENT_AUDIT.json').read_text());fresh=audit(st)
    assert original==fresh,'fresh audit changed from original'
    assert fresh['status']=='passed' and fresh['observations_replayed']==22176
    assert fresh['conditional_certificates_independently_recomputed']==6103
    assert fresh['conditional_false_certificates_all_families']==140
    original_study=json.loads((st/'RESULTS.json').read_text())
    g=json.loads((ROOT/'results/GATES.json').read_text())['gates']
    assert g['G1_in_scope_soundness']['status']=='PASSED_BOUNDED'
    assert g['G2_ood_public_safety']['status']=='PASSED_BY_ABSTENTION_ONLY'
    assert g['G8_broad_intelligence']['status']=='NOT_PASSED'
    repro=json.loads((ROOT/'results/REPRODUCIBILITY.json').read_text())
    failed=json.loads((ROOT/'results/REPRODUCIBILITY_PRECHECK_INVALID.json').read_text())
    assert repro['status']=='passed_after_excluding_total_wall_clock'
    assert failed['status']=='FAILED_BYTE_EQUALITY'
    control=json.loads((ROOT/'results/PAIRED_ANALYSIS.json').read_text())
    assert control['old_false_certifications']==78 and control['new_false_conditional_certifications']==0
    js=(ROOT/'ui/data.js').read_text();prefix='window.BGR90_DATA='
    assert js.startswith(prefix) and js.endswith(';\n')
    source_data=json.loads(js[len(prefix):-2]);assert source_data['source_sha256']==seal['results_sha256']
    assert len(source_data['examples'])==21
    previous='0'*64;receipts=[]
    for line in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines():
        receipt=json.loads(line);assert receipt['previous']==previous
        obj={k:v for k,v in receipt.items() if k!='receipt_sha256'}
        previous=hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        assert previous==receipt['receipt_sha256']
        assert sha(ROOT/receipt['source'])==receipt['source_sha256']
        receipts.append(receipt)
    assert receipts[-1]['event']=='promotion_gates'
    rows=(ROOT/'MANIFEST.sha256').read_text().splitlines()
    entries={}
    for line in rows:
        h,rel=line.split('  ',1)
        assert rel not in entries
        entries[rel]=h
    actual={rel:sha(path) for rel,path in listed().items()}
    assert actual==entries, ('manifest mismatch',set(actual)^set(entries))
    return {'schema':'bgr90.verify-release.v1','status':'passed','files':len(actual),
            'source_locked':len(lock['sha256_files']), 'source_data_sha256':seal['results_sha256'],
            'actions_replayed':fresh['observations_replayed'],
            'model_conditional_certificates_checked':fresh['conditional_certificates_independently_recomputed'],
            'conditional_false_certificates_out_of_scope':fresh['conditional_false_certificates_all_families'],
            'public_certificates_without_attestation':fresh['unattested_public_certificates'],
            'retained_original_baseline_sha256':identity['sha256'],
            'reproducibility':'all cases exactly matched; one total wall-time field excluded, original precheck failure retained',
            'validity':'bounded deterministic grammar, not universal world adequacy or AGI'}

if __name__=='__main__':print(json.dumps(verify(),indent=2))
