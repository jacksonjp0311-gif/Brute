"""Brute v0.8.0 release verification (BRUTE_PLAN_010). New file; verify_release_070 stays frozen.

Same hardening as verify_release_070 (frozen helpers of verify_release_060 reused): every JSON artifact of
results/study-010 (recursive; raw RESULTS/SCIENTIFIC excepted, they are bound by the block SEALs and their committed
.json.gz by MANIFEST) plus RELEASE.json is parsed first and its required key checked; any other exception from reused
helpers becomes VerificationError. There is a single (fast) mode: the second implementation is not re-run by the
verifier (DEVIATIONS_010 #34); its report is bound to the sealed block digests instead.

  python scripts/verify_release_080.py   # seals, freezes, regenerated paired/repro/gates, ledger, manifest, git order
"""
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check,sha,dumps
from scripts.verify_release_060 import read_bytes_,jload,req,_guard,_freeze,manifest_ok
from scripts.verify_release_070 import PREVIOUS_FREEZES as PF070

STUDY='results/study-010'
RAW=('RESULTS.json','SCIENTIFIC.json')
BLOCKS=('2x2','breadth')
# keyed by path relative to results/study-010 (block seals and the study SEAL share a file name); default 'schema'
REQUIRED_KEYS={'SEAL.json':'files_sha256','2x2/SEAL.json':'block','breadth/SEAL.json':'block','repro/2x2/SEAL.json':'block',
               'repro/breadth/SEAL.json':'block','DIAG_REPLAY_009.json':'arms','KILL_DRILL_010.json':'kill_latency_s',
               'PROGRESS_010.json':'streams','RUN_DONE_010.json':'elapsed_s','RUN_STATE_010.json':'completed_at','SEEDCHECK_010.json':'PASS'}
RELEASE_KEYS=('version','preregistration','preregistration_commit','source_freeze','source_freeze_commit','release_freeze',
              'scoring_scripts_commit','seal_commit','results_dir','gates_passed','gates_failed','GA1_010','GTI_release_statement')
PREVIOUS_FREEZES=PF070+('experiments/BRUTE_SOURCE_FREEZE_009.json','experiments/BRUTE_RELEASE_FREEZE_070_R1.json')
SCORING=('scripts/make_gates_010.py','scripts/make_paired_010.py','scripts/make_reproducibility_010.py')
LEDGER_ORDER=('preregistration_010','source_freeze_010','scoring_freeze_010','run_start_010','seal_010','gates_010')


def study_artifacts(root):
    s=Path(root)/STUDY
    return sorted(p for p in s.rglob('*.json') if p.name not in RAW and '.partial' not in p.name and 'CHECKPOINT' not in p.name)


def required_key(root,p):
    p=Path(p);root=Path(root)
    if p==root/'RELEASE.json':return 'version'
    return REQUIRED_KEYS.get(p.relative_to(root/STUDY).as_posix(),'schema')


def parse_all(root):
    out={}
    for p in study_artifacts(root)+[Path(root)/'RELEASE.json']:
        o=jload(p);req(o,required_key(root,p),str(p.relative_to(root)));out[str(p.relative_to(root))]=o
    for k in RELEASE_KEYS:req(out['RELEASE.json'],k,'RELEASE.json')
    return out


def ledger_order(receipts,root='.'):
    ev=[req(r,'event','ledger') for r in receipts]
    for e in LEDGER_ORDER:check(e in ev,'ledger lacks '+e)
    idx=[ev.index(e) for e in LEDGER_ORDER];check(idx==sorted(idx),'ledger study-010 chronology')
    end=[i for i,e in enumerate(ev) if e in ('run_end_010','stop_010')];check(end and ev.index('run_start_010')<end[0]<ev.index('seal_010'),'ledger lacks run_end_010/stop_010 between run_start and seal')
    from datetime import datetime
    def t(e,last=False):
        # Time of a receipt: the ISO time that opens its note, or, when the note has none
        # (the scoring_freeze_010 notes), the commit time of the first commit adding that receipt line.
        rs=[r for r in receipts if r['event']==e];r=rs[-1] if last else rs[0]
        try:return datetime.fromisoformat(r['note'].split()[0])
        except ValueError:pass
        g=subprocess.run(['git','log','--reverse','--format=%cI','-S'+req(r,'receipt_sha256','ledger'),'--','results/RESEARCH_LEDGER.jsonl'],cwd=root,capture_output=True,text=True)
        check(g.returncode==0 and g.stdout.split(),'cannot date ledger receipt '+e);return datetime.fromisoformat(g.stdout.split()[0])
    check((t('run_start_010')-t('scoring_freeze_010',last=True)).total_seconds()>=600,'scoring scripts ledgered < 10 min before run_start')
    return {e:next(r['note'] for r in receipts if r['event']==e)[:160] for e in ('scoring_freeze_010','run_start_010','seal_010')}


def git_order(root,rel):
    from scripts.verify_release_020 import _git
    def anc(a,b):return _git(root,'merge-base','--is-ancestor',a,b).returncode==0
    check(_git(root,'rev-parse','--git-dir').returncode==0,'not a git checkout')
    fr=jload(root/rel['source_freeze'])
    check(rel['preregistration_commit']==req(fr,'preregistration_commit','freeze'),'RELEASE.json preregistration_commit differs from the source freeze')
    chain=[('preregistration',fr['preregistration_commit']),('seedcheck',fr['seedcheck_commit']),('diagnostic',fr['diagnostic_commit']),('reference',fr['reference_commit'])]
    chain+=[(f'implementation_{i}',c) for i,c in enumerate(req(fr,'implementation_commits','freeze'))]
    chain+=[('source_freeze',rel['source_freeze_commit']),('scoring_scripts',rel['scoring_scripts_commit']),('seal',rel['seal_commit']),('head','HEAD')]
    for (na,a),(nb,b) in zip(chain,chain[1:]):
        check(anc(a,b),f'{na} {a} is not an ancestor of {nb} {b}')
        if b!='HEAD':check(_git(root,'rev-parse',a).stdout!=_git(root,'rev-parse',b).stdout,f'{na} and {nb} are the same commit')
    plan=_git(root,'show',f"{rel['preregistration_commit']}:{rel['preregistration']}")
    check(plan.returncode==0 and plan.stdout==(root/rel['preregistration']).read_text(),'plan changed after pre-registration')
    for f in SCORING:
        b=_git(root,'show',f"{rel['scoring_scripts_commit']}:{f}");check(b.returncode==0 and b.stdout==(root/f).read_text(),f'{f} changed after the scoring freeze')
    return {n:c for n,c in chain if c!='HEAD'}


def _verify(root,git):
    out={'schema':'brute.verify-release.v8_0'}
    arts=parse_all(root);rel=arts['RELEASE.json'];out['artifacts_parsed']=len(arts)
    out['manifest_files']=manifest_ok(root)
    from brute.release_version_080 import RELEASE_VERSION
    check(rel['version']==RELEASE_VERSION,'RELEASE.json version differs from brute.release_version_080')
    import tomllib
    try:pv=tomllib.loads(read_bytes_(root/'pyproject.toml').decode())['project']['version']
    except (ValueError,KeyError) as e:raise VerificationError(f'pyproject.toml: {e}') from None
    check(pv==RELEASE_VERSION,'pyproject version differs')
    out['locked_files']={f:_freeze(root,f) for f in PREVIOUS_FREEZES+(rel['source_freeze'],rel['release_freeze'])}
    for d in ('results/study-001','results/study-002','results/study-003'):
        seal=jload(root/d/'SEAL.json');check(sha(root/d/'SCIENTIFIC.json')==req(seal,'scientific_sha256',d),d+' SCIENTIFIC does not match SEAL')
    for d,mod in (('results/study-004','study004_storage'),('results/study-005','study005_storage'),('results/study-006','study006_storage'),
                  ('results/study-007','study007_storage')):
        seal=jload(root/d/'SEAL.json');__import__('scripts.'+mod,fromlist=['ensure_raw']).ensure_raw(root/d)
        for n,k in (('RESULTS.json','results_sha256'),('SCIENTIFIC.json','scientific_sha256')):check(sha(root/d/n)==req(seal,k,d),f'{d}/{n} does not match SEAL')
    from scripts.study008_storage import ensure_raw as er8;er8(root/'results/study-008')
    from scripts.study009_storage import ensure_raw as er9;er9(root/'results/study-009')
    check(rel['results_dir']==STUDY,'results_dir');s10=root/STUDY
    from scripts.study010_storage import ensure_raw;ensure_raw(s10)
    top=arts[f'{STUDY}/SEAL.json']
    for f,d in req(top,'files_sha256','study SEAL').items():
        p=s10/f
        if p.exists():check(sha(p)==d,f'study-010 {f} does not match the study SEAL')
        else:check('CHECKPOINT' in f or f.startswith('logs/') or f in ('RUN_010.log',),f'study-010 sealed file {f} is missing (only checkpoints and logs may be absent)')
    for b in BLOCKS:
        for sub in (b,f'repro/{b}'):
            sp=s10/sub/'SEAL.json'
            if not sp.exists():continue
            S=arts[f'{STUDY}/{sub}/SEAL.json']
            for n,k in (('RESULTS.json','results_sha256'),('SCIENTIFIC.json','scientific_sha256')):check(sha(s10/sub/n)==req(S,k,sub),f'study-010 {sub}/{n} does not match its SEAL')
    from scripts import make_paired_010,make_reproducibility_010,make_gates_010
    for mod,name in ((make_paired_010,'PAIRED_ANALYSIS_010.json'),(make_reproducibility_010,'REPRODUCIBILITY_010.json'),(make_gates_010,'GATES_010.json')):
        if (s10/name).exists() or name=='GATES_010.json':
            check(read_bytes_(s10/name)==dumps(mod.build(s10)),f'study-010 {name} does not regenerate byte-for-byte')
    gates=arts[f'{STUDY}/GATES_010.json']
    from scripts.verify_release_020 import ledger_020
    receipts,sup=ledger_020(root,git);out['ledger_receipts']=len(receipts);out['ledger_superseded']=sup
    out['run_chronology']=ledger_order(receipts,root)
    sources={r['source'] for r in receipts}
    for need in (rel['source_freeze'],f'{STUDY}/SEAL.json',f'{STUDY}/GATES_010.json'):check(need in sources,'ledger lacks '+need)
    if git:out['process_order']=git_order(root,rel)
    out['gates_passed']=gates['passed'];out['gates_failed']=gates['failed'];out['gates_pending']=gates['pending']
    check(rel['gates_passed']==gates['passed'] and rel['gates_failed']==gates['failed'],'RELEASE.json gate lists differ from GATES_010.json')
    for k in ('GA1_010','GD','GX2_010','G_RT'):
        if k in rel:check(rel[k]==gates[k],f'RELEASE.json {k} differs from GATES_010.json')
        out[k]=gates[k]
    out['stop_rule_fired']=gates['stop_rule_fired']
    out['status']='passed'
    out['validity']='bounded deterministic Moore worlds; 2x2 and breadth families pre-registered in BRUTE_PLAN_010; not general intelligence'
    return out


def verify(root=ROOT,fast=True,git=True):
    return _guard(_verify,Path(root),git)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--fast',action='store_true',help='accepted for symmetry; the only mode');ap.parse_args()
    try:print(json.dumps(verify(),indent=2))
    except VerificationError as e:print('VERIFICATION FAILED:',e);sys.exit(1)
