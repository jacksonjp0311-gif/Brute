"""Seed assertion for study-054 (BRUTE_PLAN_054 heldout_ranges, kept unchanged by amendment 054a: scale20t '12170001-12170006',
compat20t '12190001-12190006'; smoke range 12210001-12210006 from the plan's smoke_range). Run and ledgered (seedcheck_054) AFTER
build_authorization_054 and BEFORE any v0.51.0 run code touches a target seed. New file: check_seeds_053 logic (its helpers imported)
with the 054 ranges, the 053 target and smoke ranges added as priors. Every tracked file is scanned, .gz archives decompressed (plan 054
heldout note: compressed files were not scanned at plan time). eps 0 for both parts.
Plan rule on a hit: the part moves to the next unused prefix (1223, then 1225) by a ledgered deviation before any data.
  PYTHONPATH=. python scripts/check_seeds_054.py [--write results/diag-054/SEEDCHECK_054.json]
"""
import gzip,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check,load
from scripts.check_seeds_013 import int_pairs,_overlap
from scripts import check_seeds_045 as c45
from scripts import check_seeds_053 as c53
PLAN=ROOT/'experiments/BRUTE_PLAN_054.json';AMEND=ROOT/'experiments/BRUTE_PLAN_054a.json'
EXTRA_PRIOR={**c53.EXTRA_PRIOR,'smoke_053':c53.SMOKE,**{'plan053/'+k:v for k,v in c53.ranges_053(load(ROOT/'experiments/BRUTE_PLAN_053.json')).items()}}
SMOKE=(12210001,12210006)
FAMILY_OF={'scale20t':'scale20','compat20t':'scale16'}
EPS_OF={'scale20t':0.0,'compat20t':0.0}
COUNTS={'scale20t':6,'compat20t':6}
TOKEN=re.compile(rb'(?<![0-9.eE\-])(1[12][0-9]{6})(?![0-9.eE])');ANY=re.compile(rb"1[12][0-9]{6}");span=c45.span
SELF=('BRUTE_PLAN_054','SEEDCHECK_054','check_seeds_054')


def prior_files():
    return [ROOT/'experiments/PLAN.json']+sorted(p for p in (ROOT/'experiments').glob('BRUTE_PLAN_0*.json')
                                                 if not p.name.startswith('BRUTE_PLAN_054') and 'FREEZE' not in p.name)


def prior_ranges():
    out={}
    for p in prior_files():
        for path,r in int_pairs(load(p)):out[p.name+path]=r
    out.update(EXTRA_PRIOR);return out


def target_ranges(plan=None):
    plan=plan or load(PLAN);H=plan['heldout_ranges'];return {k:span(H[k]) for k in FAMILY_OF}


def ranges_054(plan=None):
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
    files=subprocess.run(['git','ls-files'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.split()
    files=[f for f in files if not any(s in Path(f).name for s in SELF)]
    inr=lambda v:any(a<=v<=b for a,b in ranges.values());tok=[];emb=0;scanned=0;gz=0;block=0
    for f in files:
        p=ROOT/f
        if not p.is_file():continue
        try:
            if f.endswith('.gz'):b=gzip.open(p).read();gz+=1
            else:b=p.read_bytes()
        except OSError:b=p.read_bytes()
        scanned+=1
        for m in TOKEN.finditer(b):
            v=int(m.group(1));block+=1
            if inr(v) and [f,v] not in tok:tok.append([f,v])
        emb+=sum(1 for m in ANY.finditer(b) if inr(int(m.group(0))))
    J=[c45.rule_j(f,v,ranges) for f,v in tok];K=[c45.rule_k(f,v) for f,v in tok]
    return {'files_scanned':scanned,'gz_files_decompressed':gz,'standalone_tokens_in_054_ranges':tok,'occurrences_any_in_054_ranges':emb,
            'standalone_11_12_prefix_token_count':block,'rule_j':J,'rule_k':K,'allowed':[j['allowed'] or k['allowed'] for j,k in zip(J,K)]}


NEGATIVE=(('target',12219001,None),('smoke',12219001,None),('target',12210001,None),('smoke',12170001,None),
          ('target',12170007,'scale20t'),('target',12190001,'scale20t'),('target',12190007,'compat20t'),('target',12170001,'compat20t'),
          ('target',12110001,None),('target',12090001,None),('smoke',12210007,None),('smoke',12209999,None),
          ('target',12169999,None),('target',12230001,None),('smoke',12130001,None))


def main(argv=()):
    argv=list(argv);plan=load(PLAN);amend=load(AMEND);new=ranges_054(plan);prior=prior_ranges()
    rep={'schema':'brute.seedcheck.v51','v0510_ranges':new,'prior_files':[p.name for p in prior_files()],'prior_range_count':len(prior),
         'rules_declared_before_scan':['J (cpu_jiffies, smoke only)','K (refused negative_controls probe in a SEEDCHECK file)'],
         'pairwise_overlaps':[],'prior_overlaps':[]}
    check(amend['heldout_ranges']==plan['heldout_ranges'] and amend['smoke_range']==plan['smoke_range'],'054a keeps the 054 ranges')
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
    check_run_seeds('smoke',list(range(SMOKE[0],SMOKE[1]+1)),plan);check(plan['smoke_range'].startswith('12210001-12210006'),'plan smoke_range')
    T=target_ranges(plan);rep['cases_by_key']={k:T[k][1]-T[k][0]+1 for k in COUNTS};rep['total_cases']=sum(rep['cases_by_key'].values())
    ok=(not rep['pairwise_overlaps'] and not rep['prior_overlaps'] and rep['all_tokens_allowed'] and ts['files_scanned']>0 and ts['gz_files_decompressed']>0
        and all(x[3]=='refused' for x in neg) and rep['cases_by_key']==COUNTS and rep['total_cases']==12
        and 'BRUTE_PLAN_053.json' in rep['prior_files'] and 'BRUTE_PLAN_054.json' not in rep['prior_files'])
    rep['eps_by_key']=EPS_OF;rep['PASS']=ok;txt=json.dumps(rep,indent=1,default=list);print(txt[-900:])
    if '--write' in argv:
        p=ROOT/argv[argv.index('--write')+1];p.parent.mkdir(parents=True,exist_ok=True)
        with open(p,'x') as fh:fh.write(txt+'\n')
    if not ok:raise VerificationError('seed check failed')
    return 0


if __name__=='__main__':sys.exit(main(sys.argv[1:]))
