"""Seed assertion for study-049 (BRUTE_PLAN_049 heldout_ranges: scale16 '11630001-11630012', control '11650001-11650006',
scale20 '11670001-11670008'; smoke range 11690001-11690006 from the plan's smoke_range). Run and ledgered (seedcheck_049) AFTER
build_authorization_049 and BEFORE any v0.46.0 run code touches a target seed. New file: check_seeds_048 logic (frozen; its
helpers imported) with the 049 ranges, and the 048 target and smoke ranges added as priors; every case eps 0. Parts r and c use
the sealed 048 traces, which are replays, not fresh seeds, and are excluded from this check by design.
Plan rule on a hit: the range moves to the next unused odd prefix (1169, 1173, 1175), declared in the pre-run deviation.
  PYTHONPATH=. python scripts/check_seeds_049.py [--write results/diag-049/SEEDCHECK_049.json]
"""
import gzip,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check,load
from scripts.check_seeds_013 import int_pairs,_overlap
from scripts import check_seeds_045 as c45
from scripts import check_seeds_048 as c48
PLAN=ROOT/'experiments/BRUTE_PLAN_049.json'
EXTRA_PRIOR={**c48.EXTRA_PRIOR,'smoke_048':c48.SMOKE,**{'plan048/'+k:v for k,v in c48.ranges_048(load(ROOT/'experiments/BRUTE_PLAN_048.json')).items()}}
SMOKE=(11690001,11690006)
FAMILY_OF=c48.FAMILY_OF;EPS_OF={k:0.0 for k in FAMILY_OF};COUNTS={'scale16':12,'control':6,'scale20':8}
TOKEN=c48.TOKEN;ANY=c48.ANY;span=c45.span


def prior_files():
    return [ROOT/'experiments/PLAN.json']+sorted(p for p in (ROOT/'experiments').glob('BRUTE_PLAN_0*.json')
                                                 if not p.name.startswith('BRUTE_PLAN_049') and 'FREEZE' not in p.name)


def prior_ranges():
    out={}
    for p in prior_files():
        for path,r in int_pairs(load(p)):out[p.name+path]=r
    out.update(EXTRA_PRIOR);return out


def target_ranges(plan=None):
    plan=plan or load(PLAN);H=plan['heldout_ranges'];return {k:span(H[k]) for k in FAMILY_OF}


def ranges_049(plan=None):
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
    """Every tracked file, .gz archives included (plan 049 seedcheck rule)."""
    files=subprocess.run(['git','ls-files'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.split()
    files=[f for f in files if not Path(f).name.startswith('BRUTE_PLAN_049') and 'SEEDCHECK_049' not in f and 'check_seeds_049' not in f]
    inr=lambda v:any(a<=v<=b for a,b in ranges.values());tok=[];emb=0;scanned=0;block=0
    for f in files:
        p=ROOT/f
        if not p.is_file():continue
        try:b=gzip.open(p).read() if f.endswith('.gz') else p.read_bytes()
        except OSError:b=p.read_bytes()
        scanned+=1
        for m in TOKEN.finditer(b):
            v=int(m.group(1));block+=1
            if inr(v) and [f,v] not in tok:tok.append([f,v])
        emb+=sum(1 for m in ANY.finditer(b) if inr(int(m.group(0))))
    J=[c45.rule_j(f,v,ranges) for f,v in tok];K=[c45.rule_k(f,v) for f,v in tok]
    return {'files_scanned':scanned,'standalone_tokens_in_049_ranges':tok,'occurrences_any_in_049_ranges':emb,
            'standalone_11_prefix_token_count':block,'rule_j':J,'rule_k':K,'allowed':[j['allowed'] or k['allowed'] for j,k in zip(J,K)]}


NEGATIVE=(('target',11699001,None),('smoke',11699001,None),('target',11690001,None),('smoke',11630001,None),
          ('target',11630013,'scale16'),('target',11650001,'scale16'),('target',11650007,'control'),('target',11630001,'control'),
          ('target',11670009,'scale20'),('target',11630001,'scale20'),('target',11670001,'scale16'),('target',11510001,None),
          ('target',11610001,None),('smoke',11690007,None),('smoke',11689999,None),('target',11629999,None),('target',11590001,None))


def main(argv=()):
    argv=list(argv);plan=load(PLAN);new=ranges_049(plan);prior=prior_ranges()
    rep={'schema':'brute.seedcheck.v46','v0460_ranges':new,'prior_files':[p.name for p in prior_files()],'prior_range_count':len(prior),
         'rules_declared_before_scan':['J (cpu_jiffies, smoke only)','K (refused negative_controls probe in a SEEDCHECK file)'],
         'pairwise_overlaps':[],'prior_overlaps':[]}
    ks=list(new)
    for i,a in enumerate(ks):
        for b in ks[i+1:]:
            if _overlap(new[a],new[b]):rep['pairwise_overlaps'].append([a,b])
    for a,r in new.items():
        for b,q in prior.items():
            if _overlap(r,q):rep['prior_overlaps'].append([a,b,list(q)])
    rep['token_scan']=ts=token_scan(new);rep['all_tokens_allowed']=all(ts['allowed'])
    neg=[]
    for blk,seed,k in NEGATIVE:
        try:check_run_seeds(blk,[seed],plan,key=k);neg.append([blk,seed,k,'ACCEPTED'])
        except VerificationError:neg.append([blk,seed,k,'refused'])
    rep['negative_controls']=neg
    check_run_seeds('smoke',list(range(SMOKE[0],SMOKE[1]+1)),plan);check(plan['smoke_range'].startswith('11690001-11690006'),'plan smoke_range')
    T=target_ranges(plan);rep['cases_by_key']={k:T[k][1]-T[k][0]+1 for k in COUNTS};rep['total_cases']=sum(rep['cases_by_key'].values())
    ok=(not rep['pairwise_overlaps'] and not rep['prior_overlaps'] and rep['all_tokens_allowed'] and ts['files_scanned']>0
        and all(x[3]=='refused' for x in neg) and rep['cases_by_key']==COUNTS and rep['total_cases']==26
        and 'BRUTE_PLAN_048.json' in rep['prior_files'] and 'BRUTE_PLAN_049.json' not in rep['prior_files'])
    rep['eps_by_key']=EPS_OF;rep['PASS']=ok;txt=json.dumps(rep,indent=1,default=list);print(txt[-900:])
    if '--write' in argv:
        p=ROOT/argv[argv.index('--write')+1];p.parent.mkdir(parents=True,exist_ok=True)
        with open(p,'x') as fh:fh.write(txt+'\n')
    if not ok:raise VerificationError('seed check failed')
    return 0


if __name__=='__main__':sys.exit(main(sys.argv[1:]))
