"""Brute v0.7.0 release verification (BRUTE_PLAN_009 process step 11). New file; verify_release_060 stays frozen.

Same hardening as verify_release_060 (its frozen helpers jload / read_bytes_ / req / _guard are reused): every JSON
artifact of results/study-009 (recursive; raw RESULTS/SCIENTIFIC excepted, they are bound by the block SEALs and their
committed .json.gz by MANIFEST) plus RELEASE.json is parsed first and its required key checked; any other exception
from reused helpers becomes VerificationError.

  python scripts/verify_release_070.py --fast   # seals, freezes, regenerated paired/repro/gates, ledger, manifest, git order
  python scripts/verify_release_070.py          # also re-runs the second implementation on the 2x2 + breadth + planning blocks (long)
"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check,sha,dumps
from scripts.verify_release_060 import read_bytes_,jload,req,_guard,_freeze,manifest_ok,PREVIOUS_FREEZES as PF060

STUDY='results/study-009'
RAW=('RESULTS.json','SCIENTIFIC.json')
BLOCKS=('2x2','breadth','planning')
REQUIRED_KEYS={'SEAL.json':'study','GATES_009.json':'gates','GATES_009_FINAL.json':'GTI_final_tree','PAIRED_ANALYSIS_009.json':'scientific_sha256',
               'REPRODUCIBILITY_009.json':'G12_pass','SECOND_IMPLEMENTATION_009.json':'mismatching_arm_traces','XCHECK_009.json':'per_family_arm',
               'XCHECK_SPOT_009.json':'mismatching_traces','PLANNING_AUDIT_009.json':'iv_replay','TEST_SUITE_009.json':'verdict',
               'TEST_SUITE_009_FINAL.json':'verdict','RUN_STATE_009.json':'stopped','RUN_DONE_009.json':'elapsed_s',
               'STOP_009.json':'unfinished_or_stopped','SEEDCHECK_009.json':'PASS','SPOT_SAMPLE_009.json':'cases','DIAG_LAG_009.json':'arms',
               'RELEASE.json':'version'}
RELEASE_KEYS=('version','preregistration','preregistration_commit','source_freeze','source_freeze_commit','release_freeze',
              'scoring_scripts_commit','seal_commit','results_dir','gates_passed','gates_failed','GA1_prime','GP1','GTI_release_statement')
PREVIOUS_FREEZES=PF060+('experiments/BRUTE_SOURCE_FREEZE_008.json','experiments/BRUTE_RELEASE_FREEZE_060.json','experiments/BRUTE_RELEASE_FREEZE_060_R1.json')
SCORING=('scripts/make_gates_009.py','scripts/make_paired_009.py','scripts/make_reproducibility_009.py')
LEDGER_ORDER=('preregistration_009','seedcheck_009','diagnostic_009','second_implementation_009','source_freeze_009','scoring_freeze_009',
              'run_start_009','seal_009','gates_009')


def study_artifacts(root):
    s=Path(root)/STUDY
    return sorted(p for p in s.rglob('*.json') if p.name not in RAW and '.partial' not in p.name)


def parse_all(root):
    out={}
    for p in study_artifacts(root)+[Path(root)/'RELEASE.json']:
        o=jload(p);k=REQUIRED_KEYS.get(p.name,'schema');req(o,k,str(p.relative_to(root)));out[str(p.relative_to(root))]=o
    for k in RELEASE_KEYS:req(out['RELEASE.json'],k,'RELEASE.json')
    return out


def ledger_order(receipts):
    ev=[req(r,'event','ledger') for r in receipts]
    for e in LEDGER_ORDER:check(e in ev,'ledger lacks '+e)
    idx=[ev.index(e) for e in LEDGER_ORDER];check(idx==sorted(idx),'ledger study-009 chronology')
    end=[i for i,e in enumerate(ev) if e in ('run_end_009','stop_009')];check(end and ev.index('run_start_009')<end[0]<ev.index('seal_009'),'ledger lacks run_end_009/stop_009 between run_start and seal')
    from datetime import datetime
    t=lambda e:datetime.fromisoformat(next(r['note'] for r in receipts if r['event']==e).split()[0])
    check((t('run_start_009')-t('scoring_freeze_009')).total_seconds()>=600,'scoring scripts ledgered < 10 min before run_start')
    return {e:next(r['note'] for r in receipts if r['event']==e)[:160] for e in ('scoring_freeze_009','run_start_009','seal_009')}


def git_order(root,rel):
    from scripts.verify_release_020 import _git
    def anc(a,b):return _git(root,'merge-base','--is-ancestor',a,b).returncode==0
    check(_git(root,'rev-parse','--git-dir').returncode==0,'not a git checkout')
    fr=jload(root/rel['source_freeze'])
    chain=[('preregistration',req(fr,'preregistration_commit','freeze')),('seedcheck',fr['seedcheck_commit']),('diagnostic',fr['diagnostic_commit']),
           ('reference',fr['reference_commit']),('adopted',fr['adopted_files_commit'])]
    chain+=[(f'implementation_{i}',c) for i,c in enumerate(req(fr,'implementation_commits','freeze'))]
    chain+=[('source_freeze',rel['source_freeze_commit']),('scoring_scripts',rel['scoring_scripts_commit']),('seal',rel['seal_commit']),('head','HEAD')]
    for (na,a),(nb,b) in zip(chain,chain[1:]):
        check(anc(a,b),f'{na} {a} is not an ancestor of {nb} {b}')
        if b!='HEAD':check(_git(root,'rev-parse',a).stdout!=_git(root,'rev-parse',b).stdout,f'{na} and {nb} are the same commit')
    plan=_git(root,'show',f"{fr['preregistration_commit']}:{rel['preregistration']}")
    check(plan.returncode==0 and plan.stdout==(root/rel['preregistration']).read_text(),'plan changed after pre-registration')
    for f in SCORING:
        b=_git(root,'show',f"{rel['scoring_scripts_commit']}:{f}");check(b.returncode==0 and b.stdout==(root/f).read_text(),f'{f} changed after the scoring freeze')
    return {n:c for n,c in chain if c!='HEAD'}


def _verify(root,fast,git):
    out={'schema':'brute.verify-release.v7_0'}
    arts=parse_all(root);rel=arts['RELEASE.json'];out['artifacts_parsed']=len(arts)
    out['manifest_files']=manifest_ok(root)
    from brute.release_version_070 import RELEASE_VERSION
    check(rel['version']==RELEASE_VERSION,'RELEASE.json version differs from brute.release_version_070')
    import tomllib
    try:pv=tomllib.loads(read_bytes_(root/'pyproject.toml').decode())['project']['version']
    except (ValueError,KeyError) as e:raise VerificationError(f'pyproject.toml: {e}') from None
    check(pv==RELEASE_VERSION,'pyproject version differs')
    out['locked_files']={f:_freeze(root,f) for f in PREVIOUS_FREEZES+(rel['source_freeze'],rel['release_freeze'])}
    fz=jload(root/rel['source_freeze'])
    for f,d in req(fz,'adopted_files','freeze').items():check(sha(root/f)==d,f'adopted file {f} changed')
    for d in ('results/study-001','results/study-002','results/study-003'):
        seal=jload(root/d/'SEAL.json');check(sha(root/d/'SCIENTIFIC.json')==req(seal,'scientific_sha256',d),d+' SCIENTIFIC does not match SEAL')
    for d,mod in (('results/study-004','study004_storage'),('results/study-005','study005_storage'),('results/study-006','study006_storage'),
                  ('results/study-007','study007_storage')):
        seal=jload(root/d/'SEAL.json');__import__('scripts.'+mod,fromlist=['ensure_raw']).ensure_raw(root/d)
        for n,k in (('RESULTS.json','results_sha256'),('SCIENTIFIC.json','scientific_sha256')):check(sha(root/d/n)==req(seal,k,d),f'{d}/{n} does not match SEAL')
    from scripts.study008_storage import ensure_raw as er8;er8(root/'results/study-008')
    check(rel['results_dir']==STUDY,'results_dir');s9=root/STUDY
    from scripts.study009_storage import ensure_raw;ensure_raw(s9)
    top=arts[f'{STUDY}/SEAL.json']
    for f,d in req(top,'files_sha256','study SEAL').items():
        p=s9/f
        if p.exists():check(sha(p)==d,f'study-009 {f} does not match the study SEAL')
        else:check('CHECKPOINT' in f and f.endswith('.jsonl'),f'study-009 sealed file {f} is missing (only CHECKPOINT*.jsonl may be absent)')
    for b in BLOCKS:
        for sub in (b,f'repro/{b}'):
            sp=s9/sub/'SEAL.json'
            if not sp.exists():continue
            S=arts[f'{STUDY}/{sub}/SEAL.json']
            for n,k in (('RESULTS.json','results_sha256'),('SCIENTIFIC.json','scientific_sha256')):check(sha(s9/sub/n)==req(S,k,sub),f'study-009 {sub}/{n} does not match its SEAL')
            check(sha(root/rel['preregistration'])==S['plan_sha256'] and sha(root/rel['source_freeze'])==S['freeze_sha256'],f'study-009 {sub} plan/freeze')
    from scripts import make_paired_009,make_reproducibility_009,make_gates_009
    for mod,name in ((make_paired_009,'PAIRED_ANALYSIS_009.json'),(make_reproducibility_009,'REPRODUCIBILITY_009.json'),(make_gates_009,'GATES_009.json')):
        if (s9/name).exists() or name=='GATES_009.json':
            check(read_bytes_(s9/name)==dumps(mod.build(s9)),f'study-009 {name} does not regenerate byte-for-byte')
    gates=arts[f'{STUDY}/GATES_009.json']
    if (s9/'GATES_009_FINAL.json').exists():
        from scripts.make_gates_final_009 import build as final
        check(read_bytes_(s9/'GATES_009_FINAL.json')==dumps(final(s9)),'GATES_009_FINAL.json does not regenerate byte-for-byte')
        out['GTI_final_tree']=arts[f'{STUDY}/GATES_009_FINAL.json']['GTI_final_tree']['pass']
    si=arts.get(f'{STUDY}/SECOND_IMPLEMENTATION_009.json')
    if si:
        for p,v in req(si,'results_files_sha256','second implementation').items():
            b=Path(p).parent.name;check(b in BLOCKS and v==arts[f'{STUDY}/{b}/SEAL.json']['results_sha256'],'second implementation is of other results: '+p)
    if not fast:
        from experiments import v070_reference as R
        from experiments.brute_common import load as _l
        cases=[];[cases.extend(jload(s9/b/'RESULTS.json')['cases']) for b in BLOCKS if (s9/b/'RESULTS.json').exists()]
        again=R.run(cases,_l(R.PLAN),workers=6,mutate_k=20,source_sha=sha(root/'experiments/v070_reference.py'))
        drop=('results_files_sha256','cases','wall_informational')
        check(json.loads(json.dumps(again,sort_keys=True))=={k:v for k,v in si.items() if k not in drop},'second implementation does not reproduce')
        out['second_implementation']='re-run, identical'
    from scripts.verify_release_020 import ledger_020
    receipts,sup=ledger_020(root,git);out['ledger_receipts']=len(receipts);out['ledger_superseded']=sup
    out['run_chronology']=ledger_order(receipts)
    sources={r['source'] for r in receipts}
    for need in (rel['preregistration'],rel['source_freeze'],f'{STUDY}/SEAL.json',f'{STUDY}/GATES_009.json'):check(need in sources,'ledger lacks '+need)
    if git:out['process_order']=git_order(root,rel)
    out['gates_passed']=gates['passed'];out['gates_failed']=gates['failed'];out['gates_pending']=gates['pending']
    check(rel['gates_passed']==gates['passed'] and rel['gates_failed']==gates['failed'],'RELEASE.json gate lists differ from GATES_009.json')
    for k in ('GA1_prime','GP1','GX2_dprime','G_RT'):
        if k in rel:check(rel[k]==gates[k],f'RELEASE.json {k} differs from GATES_009.json')
        out[k]=gates[k]
    out['stop_rule_fired']=gates['stop_rule_fired']
    out['status']='passed'
    out['validity']='bounded deterministic Moore worlds; 2x2, planning and breadth families pre-registered in BRUTE_PLAN_009; not general intelligence'
    return out


def verify(root=ROOT,fast=False,git=True):
    return _guard(_verify,Path(root),fast,git)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--fast',action='store_true');a=ap.parse_args()
    try:print(json.dumps(verify(fast=a.fast),indent=2))
    except VerificationError as e:print('VERIFICATION FAILED:',e);sys.exit(1)
