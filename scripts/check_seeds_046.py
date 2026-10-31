"""Seed assertion for study-046 (BRUTE_PLAN_046 heldout_ranges: scale16 '11230001-11230012', control '11270001-11270006';
smoke range 11370001-11370006 from the plan's smoke_range). Run and ledgered (seedcheck_046) AFTER build_authorization_046 and
BEFORE any v0.43.0 run code touches a target seed. New file: check_seeds_045 logic (frozen, imported) with the 046 ranges, and the
045 target ranges and 045 smoke range added as priors; every case eps 0. Part a_replay uses the sealed 045 traces (seeds
11130001-11130012, 11190001-11190006), which are replays, not fresh seeds, and are excluded from this check by design.

Adjudication rules J and K are those of check_seeds_045 (declared in that file before its scan, and re-declared here before this
scan). Plan rule on a hit: the range moves to the next unused odd prefix (1131, 1133), declared in the pre-run deviation.
  PYTHONPATH=. python scripts/check_seeds_046.py [--write results/diag-046/SEEDCHECK_046.json]
"""
import gzip,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check,load
from scripts.check_seeds_013 import int_pairs,_overlap
from scripts import check_seeds_033 as c33
from scripts import check_seeds_045 as c45
PLAN=ROOT/'experiments/BRUTE_PLAN_046.json'
EXTRA_PRIOR={**c45.EXTRA_PRIOR,'smoke_045':c45.SMOKE,**{'plan045/'+k:v for k,v in c45.ranges_045().items()}}
SMOKE=(11370001,11370006)
FAMILY_OF={'scale16':'scale16','control':'control_cycle3'}
EPS_OF={k:0.0 for k in FAMILY_OF}
COUNTS={'scale16':12,'control':6}
TOKEN=re.compile(rb'(?<![0-9.eE\-])(11[0-9]{6})(?![0-9.eE])');ANY=re.compile(rb"11[0-9]{6}")
span=c45.span


def prior_files():
    return [ROOT/'experiments/PLAN.json']+sorted(p for p in (ROOT/'experiments').glob('BRUTE_PLAN_0*.json')
                                                 if not p.name.startswith('BRUTE_PLAN_046') and 'FREEZE' not in p.name)


def prior_ranges():
    out={}
    for p in prior_files():
        for path,r in int_pairs(load(p)):out[p.name+path]=r
    out.update(EXTRA_PRIOR);return out


def target_ranges(plan=None):
    plan=plan or load(PLAN);H=plan['heldout_ranges'];return {k:span(H[k]) for k in FAMILY_OF}


def ranges_046(plan=None):
    plan=plan or load(PLAN);out={'target/'+k:r for k,r in target_ranges(plan).items()}
    out['smoke']=SMOKE;return out


def check_run_seeds(block,seeds,plan=None,key=None):
    plan=plan or load(PLAN)
    if block=='smoke':
        bad=[s for s in seeds if not (SMOKE[0]<=s<=SMOKE[1])];check(not bad,f'smoke seed outside {SMOKE}: {bad[:5]}');return True
    if block!='target':raise VerificationError('unknown block '+str(block))
    R=target_ranges(plan)
    if key is not None:check(key in R,f'key {key} not in block {block}')
    ks=[key] if key else list(R)
    bad=[s for s in seeds if not any(R[k][0]<=s<=R[k][1] for k in ks)]
    check(not bad,f'{block} seed outside its declared range: {bad[:5]}');return True


def token_scan(ranges):
    files=subprocess.run(['git','ls-files','results','experiments'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.split()
    files=[f for f in files if f.endswith(c33.SCAN_SUFFIX) and not Path(f).name.startswith('BRUTE_PLAN_046') and 'SEEDCHECK_046' not in f]
    inr=lambda v:any(a<=v<=b for a,b in ranges.values());tok=[];emb=0;scanned=0;block=0
    for f in files:
        p=ROOT/f
        if not p.exists():continue
        b=gzip.open(p).read() if f.endswith('.gz') else p.read_bytes();scanned+=1
        for m in TOKEN.finditer(b):
            v=int(m.group(1));block+=1
            if inr(v) and [f,v] not in tok:tok.append([f,v])
        emb+=sum(1 for m in ANY.finditer(b) if inr(int(m.group(0))))
    J=[c45.rule_j(f,v,ranges) for f,v in tok];K=[c45.rule_k(f,v) for f,v in tok]
    return {'files_scanned':scanned,'standalone_tokens_in_046_ranges':tok,'occurrences_any_in_046_ranges':emb,
            'standalone_11_prefix_token_count':block,'rule_j':J,'rule_k':K,'allowed':[j['allowed'] or k['allowed'] for j,k in zip(J,K)]}


NEGATIVE=(('target',11379001,None),('smoke',11379001,None),('target',11370001,None),('smoke',11230001,None),
          ('target',11230013,'scale16'),('target',11270001,'scale16'),('target',11270007,'control'),('target',11230001,'control'),
          ('target',11130001,None),('target',11190001,None),('target',11290001,None),('target',11310001,None),
          ('smoke',11370007,None),('smoke',11369999,None),('target',11229999,None),('target',11240001,None))


def main(argv=()):
    argv=list(argv);plan=load(PLAN);new=ranges_046(plan);prior=prior_ranges()
    rep={'schema':'brute.seedcheck.v43','v0430_ranges':new,'prior_files':[p.name for p in prior_files()],'prior_range_count':len(prior),
         'rules_declared_before_scan':['J (cpu_jiffies, smoke only)','K (refused negative_controls probe in a SEEDCHECK file)'],
         'pairwise_overlaps':[],'prior_overlaps':[]}
    ks=list(new)
    for i,a in enumerate(ks):
        for b in ks[i+1:]:
            if _overlap(new[a],new[b]):rep['pairwise_overlaps'].append([a,b])
    for a,r in new.items():
        for b,q in prior.items():
            if _overlap(r,q):rep['prior_overlaps'].append([a,b,list(q)])
    rep['token_scan']=ts=token_scan(new)
    rep['all_tokens_allowed']=all(ts['allowed'])
    neg=[]
    for blk,seed,k in NEGATIVE:
        try:check_run_seeds(blk,[seed],plan,key=k);neg.append([blk,seed,k,'ACCEPTED'])
        except VerificationError:neg.append([blk,seed,k,'refused'])
    rep['negative_controls']=neg
    check_run_seeds('smoke',list(range(SMOKE[0],SMOKE[1]+1)),plan);check(plan['smoke_range'].startswith('11370001-11370006'),'plan smoke_range')
    T=target_ranges(plan);rep['cases_by_key']={k:T[k][1]-T[k][0]+1 for k in COUNTS};rep['total_cases']=sum(rep['cases_by_key'].values())
    ok=(not rep['pairwise_overlaps'] and not rep['prior_overlaps'] and rep['all_tokens_allowed'] and ts['files_scanned']>0
        and all(x[3]=='refused' for x in neg) and rep['cases_by_key']==COUNTS and rep['total_cases']==18==plan['cases']['total_fresh']
        and 'BRUTE_PLAN_045.json' in rep['prior_files'] and 'BRUTE_PLAN_046.json' not in rep['prior_files'])
    rep['eps_by_key']=EPS_OF;rep['PASS']=ok;txt=json.dumps(rep,indent=1,default=list);print(txt[-900:])
    if '--write' in argv:
        p=ROOT/argv[argv.index('--write')+1];p.parent.mkdir(parents=True,exist_ok=True)
        with open(p,'x') as fh:fh.write(txt+'\n')
    if not ok:raise VerificationError('seed check failed')
    return 0


if __name__=='__main__':sys.exit(main(sys.argv[1:]))
