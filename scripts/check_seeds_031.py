"""Seed assertion for study-031 (BRUTE_PLAN_031 heldout_ranges incl. smoke 9790001-9790030). Run and ledgered
(seedcheck_031) BEFORE any v0.28.0 run code touches a target seed. New file (check_seeds_030 logic with 031 ranges;
scale16 has 18 seeds; stress = first 3 seeds of scale12/16 at eps 0.05).

Asserts (exit 0 iff all hold):
  1. the 031 ranges (4 targets + smoke) are pairwise disjoint;
  2. disjoint from every [lo, hi] integer pair in experiments/PLAN.json and every experiments/BRUTE_PLAN_0*.json except
     BRUTE_PLAN_031* (parsed, not hard-coded) plus the extra ranges of check_seeds_030 and 9690001-9690030 (030 smoke);
  3. token scan: no git-tracked file under results/ or experiments/ (json, jsonl, txt, md, json.gz; BRUTE_PLAN_031* and
     this check's own output excluded) contains a standalone integer token (not preceded or followed by a digit, '.',
     'e' or '-') in any 031 range; digit runs inside longer numbers (e.g. 40.19249896100018) are counted and reported
     as embedded, not as seeds;
  4. check_run_seeds(block, seeds) refuses any seed outside its declared block range (negative controls);
  5. 48 target seeds -> 48 main cases (eps 0) + 6 stress cases (first 3 seeds of scale12/16, eps 0.05) = 54.
  PYTHONPATH=. python scripts/check_seeds_031.py [--write results/diag-031/SEEDCHECK_031.json]
"""
import gzip,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check,load
from scripts.check_seeds_013 import int_pairs,_overlap
from scripts.check_seeds_030 import EXTRA_PRIOR as EXTRA_030
PLAN=ROOT/'experiments/BRUTE_PLAN_031.json'
EXTRA_PRIOR={**EXTRA_030,'smoke_030':(9690001,9690030)}
SMOKE=(9790001,9790030)
FAMILIES=('scale8','scale12','scale16','control_cycle3');STRESS_FAMILIES=('scale12','scale16')
EPS_MAIN=(0.0,);EPS_STRESS=0.05;STRESS_PER_FAMILY=3
TOKEN=re.compile(rb'(?<![0-9.eE\-])(97[0-9]{5})(?![0-9.eE])');ANY=re.compile(rb'97[0-9]{5}')
SCAN_SUFFIX=('.json','.jsonl','.txt','.md','.json.gz')


def prior_files():
    return [ROOT/'experiments/PLAN.json']+sorted(p for p in (ROOT/'experiments').glob('BRUTE_PLAN_0*.json')
                                                 if not p.name.startswith('BRUTE_PLAN_031') and 'FREEZE' not in p.name)


def prior_ranges():
    out={}
    for p in prior_files():
        for path,r in int_pairs(load(p)):out[p.name+path]=r
    out.update(EXTRA_PRIOR);return out


def ranges_031(plan=None):
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
    files=[f for f in files if f.endswith(SCAN_SUFFIX) and not Path(f).name.startswith('BRUTE_PLAN_031') and 'SEEDCHECK_031' not in f]
    inr=lambda v:any(a<=v<=b for a,b in ranges.values());tok=[];emb=0;scanned=0
    for f in files:
        p=ROOT/f
        if not p.exists():continue
        b=gzip.open(p).read() if f.endswith('.gz') else p.read_bytes();scanned+=1
        for m in TOKEN.finditer(b):
            if inr(int(m.group(1))):tok.append([f,int(m.group(1))])
        emb+=sum(1 for m in ANY.finditer(b) if inr(int(m.group(0))))
    return {'files_scanned':scanned,'standalone_tokens_in_031_ranges':tok,'occurrences_any_in_031_ranges':emb,
            'embedded_only':emb-len(tok)}


NEGATIVE=(('target',9799001,None),('smoke',9799001,None),('target',9790001,None),('smoke',9710001,None),('target',9710013,'scale8'),
          ('target',9720001,'scale8'),('target',9740007,'control_cycle3'),('target',9610001,None),('smoke',9690001,None),('target',9730019,None),
          ('smoke',9790031,None),('target',9709999,None),('target',9720013,'scale12'))


def main(argv=()):
    argv=list(argv);plan=load(PLAN);new=ranges_031(plan);prior=prior_ranges()
    rep={'schema':'brute.seedcheck.v28','v0280_ranges':new,'prior_files':[p.name for p in prior_files()],'prior_range_count':len(prior),
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
    rep['target_seeds']=seeds;rep['main_cases']=seeds*len(EPS_MAIN);rep['stress_cases']=STRESS_PER_FAMILY*len(STRESS_FAMILIES)
    rep['total_cases']=rep['main_cases']+rep['stress_cases']
    ok=(not rep['pairwise_overlaps'] and not rep['prior_overlaps'] and not rep['token_scan']['standalone_tokens_in_031_ranges']
        and rep['token_scan']['files_scanned']>0 and all(x[2]=='refused' for x in neg) and seeds==48
        and rep['main_cases']==48 and rep['stress_cases']==6 and rep['total_cases']==54 and 'BRUTE_PLAN_030.json' in rep['prior_files']
        and 'BRUTE_PLAN_031.json' not in rep['prior_files'])
    rep['PASS']=ok;txt=json.dumps(rep,indent=1,default=list);print(txt)
    if '--write' in argv:
        p=ROOT/argv[argv.index('--write')+1];p.parent.mkdir(parents=True,exist_ok=True)
        with open(p,'x') as fh:fh.write(txt+'\n')
    if not ok:raise VerificationError('seed check failed')
    return 0


if __name__=='__main__':sys.exit(main(sys.argv[1:]))
