"""Seed assertion for study-032 (BRUTE_PLAN_032 heldout_ranges incl. smoke 9890001-9890030). Run and ledgered
(seedcheck_032) BEFORE any v0.29.0 run code touches a target seed. New file (check_seeds_031 logic with 032 ranges:
noisy_scale8/12/16 at eps 0.05 = 30 cases; clean regression = first 6 noisy_scale12 and first 6 noisy_scale16 seeds at
eps 0 = 12 cases; controls 6 at eps 0; total 48).

Asserts (exit 0 iff all hold):
  1. the 032 ranges (4 targets + smoke) are pairwise disjoint;
  2. disjoint from every [lo, hi] integer pair in experiments/PLAN.json and every experiments/BRUTE_PLAN_0*.json except
     BRUTE_PLAN_032* (parsed, not hard-coded) plus the extra ranges of check_seeds_031 and 9790001-9790030 (031 smoke);
  3. token scan: no git-tracked file under results/ or experiments/ (json, jsonl, txt, md, json.gz; BRUTE_PLAN_032* and
     this check's own output excluded) contains a standalone integer token (not preceded or followed by a digit, '.',
     'e' or '-') in any 032 range; digit runs inside longer numbers (e.g. 40.19249896100018) are counted and reported
     as embedded, not as seeds;
  4. check_run_seeds(block, seeds) refuses any seed outside its declared block range (negative controls);
  5. 36 target seeds -> 30 noisy cases (eps 0.05) + 12 clean regression cases + 6 controls (eps 0) = 48.
  PYTHONPATH=. python scripts/check_seeds_032.py [--write results/diag-032/SEEDCHECK_032.json]
"""
import gzip,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check,load
from scripts.check_seeds_013 import int_pairs,_overlap
from scripts.check_seeds_031 import EXTRA_PRIOR as EXTRA_031
PLAN=ROOT/'experiments/BRUTE_PLAN_032.json'
EXTRA_PRIOR={**EXTRA_031,'smoke_031':(9790001,9790030)}
SMOKE=(9890001,9890030)
FAMILIES=('noisy_scale8','noisy_scale12','noisy_scale16','control_cycle3');NOISY=('noisy_scale8','noisy_scale12','noisy_scale16')
CLEAN_FAMILIES=('noisy_scale12','noisy_scale16');CLEAN_PER_FAMILY=6
TOKEN=re.compile(rb'(?<![0-9.eE\-])(98[0-9]{5})(?![0-9.eE])');ANY=re.compile(rb'98[0-9]{5}')
SCAN_SUFFIX=('.json','.jsonl','.txt','.md','.json.gz')


def prior_files():
    return [ROOT/'experiments/PLAN.json']+sorted(p for p in (ROOT/'experiments').glob('BRUTE_PLAN_0*.json')
                                                 if not p.name.startswith('BRUTE_PLAN_032') and 'FREEZE' not in p.name)


def prior_ranges():
    out={}
    for p in prior_files():
        for path,r in int_pairs(load(p)):out[p.name+path]=r
    out.update(EXTRA_PRIOR);return out


def ranges_032(plan=None):
    plan=plan or load(PLAN);out={'target/'+f:tuple(r) for f,r in plan['heldout_ranges']['targets'].items()};out['smoke']=SMOKE;return out


def check_run_seeds(block,seeds,plan=None,family=None):
    plan=plan or load(PLAN)
    if block=='smoke':
        bad=[s for s in seeds if not (SMOKE[0]<=s<=SMOKE[1])];check(not bad,f'smoke seed outside {SMOKE}: {bad[:5]}');return True
    if block!='target':raise VerificationError('unknown block '+str(block))
    R=plan['heldout_ranges']['targets']
    if family is not None:check(family in R,f'family {family} not in block {block}')
    fams=[family] if family else list(R)
    bad=[s for s in seeds if not any(R[f][0]<=s<=R[f][1] for f in fams)]
    check(not bad,f'{block} seed outside its declared range: {bad[:5]}');return True


def token_scan(ranges):
    files=subprocess.run(['git','ls-files','results','experiments'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.split()
    files=[f for f in files if f.endswith(SCAN_SUFFIX) and not Path(f).name.startswith('BRUTE_PLAN_032') and 'SEEDCHECK_032' not in f]
    inr=lambda v:any(a<=v<=b for a,b in ranges.values());tok=[];emb=0;scanned=0
    for f in files:
        p=ROOT/f
        if not p.exists():continue
        b=gzip.open(p).read() if f.endswith('.gz') else p.read_bytes();scanned+=1
        for m in TOKEN.finditer(b):
            if inr(int(m.group(1))):tok.append([f,int(m.group(1))])
        emb+=sum(1 for m in ANY.finditer(b) if inr(int(m.group(0))))
    return {'files_scanned':scanned,'standalone_tokens_in_032_ranges':tok,'occurrences_any_in_032_ranges':emb,
            'embedded_only':emb-len(tok)}


NEGATIVE=(('target',9899001,None),('smoke',9899001,None),('target',9890001,None),('smoke',9810001,None),('target',9810013,'noisy_scale8'),
          ('target',9820001,'noisy_scale8'),('target',9840007,'control_cycle3'),('target',9710001,None),('smoke',9790001,None),('target',9830007,None),
          ('smoke',9890031,None),('target',9809999,None),('target',9820013,'noisy_scale12'),('target',9840022,None))


def main(argv=()):
    argv=list(argv);plan=load(PLAN);new=ranges_032(plan);prior=prior_ranges()
    rep={'schema':'brute.seedcheck.v29','v0290_ranges':new,'prior_files':[p.name for p in prior_files()],'prior_range_count':len(prior),
         'pairwise_overlaps':[],'prior_overlaps':[]}
    ks=list(new)
    for i,a in enumerate(ks):
        for b in ks[i+1:]:
            if _overlap(new[a],new[b]):rep['pairwise_overlaps'].append([a,b])
    for a,r in new.items():
        for b,q in prior.items():
            if _overlap(r,q):rep['prior_overlaps'].append([a,b,list(q)])
    rep['token_scan']=token_scan(new)
    neg=[]
    for blk,seed,fam in NEGATIVE:
        try:check_run_seeds(blk,[seed],plan,family=fam);neg.append([blk,seed,'ACCEPTED'])
        except VerificationError:neg.append([blk,seed,'refused'])
    rep['negative_controls']=neg
    check_run_seeds('smoke',list(range(SMOKE[0],SMOKE[1]+1)),plan)
    T=plan['heldout_ranges']['targets'];check(sorted(T)==sorted(FAMILIES),'target families')
    check(tuple(plan['heldout_ranges']['smoke'])==SMOKE,'plan smoke range')
    seeds=sum(T[f][1]-T[f][0]+1 for f in FAMILIES)
    rep['target_seeds']=seeds;rep['noisy_cases']=sum(T[f][1]-T[f][0]+1 for f in NOISY);rep['clean_cases']=CLEAN_PER_FAMILY*len(CLEAN_FAMILIES)
    rep['control_cases']=T['control_cycle3'][1]-T['control_cycle3'][0]+1;rep['total_cases']=rep['noisy_cases']+rep['clean_cases']+rep['control_cases']
    ok=(not rep['pairwise_overlaps'] and not rep['prior_overlaps'] and not rep['token_scan']['standalone_tokens_in_032_ranges']
        and rep['token_scan']['files_scanned']>0 and all(x[2]=='refused' for x in neg) and seeds==36
        and rep['noisy_cases']==30 and rep['clean_cases']==12 and rep['control_cases']==6 and rep['total_cases']==48
        and 'BRUTE_PLAN_031.json' in rep['prior_files'] and 'BRUTE_PLAN_032.json' not in rep['prior_files'])
    rep['PASS']=ok;txt=json.dumps(rep,indent=1,default=list);print(txt)
    if '--write' in argv:
        p=ROOT/argv[argv.index('--write')+1];p.parent.mkdir(parents=True,exist_ok=True)
        with open(p,'x') as fh:fh.write(txt+'\n')
    if not ok:raise VerificationError('seed check failed')
    return 0


if __name__=='__main__':sys.exit(main(sys.argv[1:]))
