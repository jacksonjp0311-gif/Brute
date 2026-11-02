"""Seed assertion for study-058 (BRUTE_PLAN_058 heldout_ranges: scale20b '12530001-12530012'; smoke range 12550001-12550006 from
the plan's smoke_range). Run and ledgered (seedcheck_058) AFTER build_authorization_058, BEFORE the study tooling is committed and
before any run code touches a fresh seed. New file: the check_seeds_057 logic (rules J, K, L) with the 058 ranges; the 056 and 057
target and smoke ranges are priors.
Every tracked file is scanned, .gz archives decompressed. eps 0 for both parts.
Plan rule on a hit: the part moves to the next unused odd prefix (1257, then 1259) by a ledgered deviation before any data.
  PYTHONPATH=. python scripts/check_seeds_058.py [--write results/diag-058/SEEDCHECK_058.json]
"""
import gzip,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check,load
from scripts.check_seeds_013 import int_pairs,_overlap
from scripts import check_seeds_045 as c45
from scripts import check_seeds_057 as c57
PLAN=ROOT/'experiments/BRUTE_PLAN_058.json'
EXTRA_PRIOR={**c57.EXTRA_PRIOR,'smoke_057':c57.SMOKE,**{'plan057/'+k:v for k,v in c57.ranges_057(load(ROOT/'experiments/BRUTE_PLAN_057.json')).items()}}
SMOKE=(12550001,12550006)
FAMILY_OF={'scale20b':'scale20'}
EPS_OF={'scale20b':0.0}
COUNTS={'scale20b':12}
TOKEN=re.compile(rb'(?<![0-9.eE\-])(1[12][0-9]{6})(?![0-9.eE])');ANY=re.compile(rb"1[12][0-9]{6}");span=c45.span
SELF=('BRUTE_PLAN_058','SEEDCHECK_058','check_seeds_058')


def prior_files():
    return [ROOT/'experiments/PLAN.json']+sorted(p for p in (ROOT/'experiments').glob('BRUTE_PLAN_0*.json')
                                                 if not p.name.startswith('BRUTE_PLAN_058') and 'FREEZE' not in p.name)


def prior_ranges():
    out={}
    for p in prior_files():
        for path,r in int_pairs(load(p)):out[p.name+path]=r
    out.update(EXTRA_PRIOR);return out


def target_ranges(plan=None):
    plan=plan or load(PLAN);H=plan['heldout_ranges'];return {k:span(H[k]) for k in FAMILY_OF}


def ranges_058(plan=None):
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


OWN=re.compile(r'^(experiments|scripts|tests)/[a-z0-9_]+_(058|0550)\.py$')


def rule_l(f,v,ranges):
    """Rule L (carried from 055 #183, declared here before any scan): a standalone token that lies in the 058 smoke range
    and in no 058 target range is allowed in this study's own tooling source (experiments|scripts|tests/*_058.py or *_0550.py),
    where the plan's smoke seeds are declared. Target-range tokens are never allowed by L."""
    hit=[k for k,(a,b) in ranges.items() if a<=v<=b];smoke_only=hit==['smoke'];own=bool(OWN.match(f))
    return {'file':f,'token':v,'ranges':hit,'smoke_only':smoke_only,'own_study_source':own,'allowed':smoke_only and own}


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
    J=[c45.rule_j(f,v,ranges) for f,v in tok];K=[c45.rule_k(f,v) for f,v in tok];L=[rule_l(f,v,ranges) for f,v in tok]
    return {'files_scanned':scanned,'gz_files_decompressed':gz,'standalone_tokens_in_058_ranges':tok,'occurrences_any_in_058_ranges':emb,
            'standalone_11_12_prefix_token_count':block,'rule_j':J,'rule_k':K,'rule_l':L,
            'allowed':[j['allowed'] or k['allowed'] or l['allowed'] for j,k,l in zip(J,K,L)]}


NEGATIVE=(('target',12559001,None),('smoke',12559001,None),('target',12550001,None),('smoke',12530001,None),
          ('target',12530013,'scale20b'),('target',12410001,'scale20b'),('target',12430001,None),('target',12410012,None),
          ('target',12330001,None),('target',12350001,None),('smoke',12550007,None),('smoke',12549999,None),
          ('target',12529999,None),('target',12570001,None),('smoke',12430001,None))


def main(argv=()):
    argv=list(argv);plan=load(PLAN);new=ranges_058(plan);prior=prior_ranges()
    rep={'schema':'brute.seedcheck.v55','v0550_ranges':new,'prior_files':[p.name for p in prior_files()],'prior_range_count':len(prior),
         'rules_declared_before_scan':['J (cpu_jiffies, smoke only)','K (refused negative_controls probe in a SEEDCHECK file)',
                                   'L (058 smoke-range token in study-058 own tooling source; carried from 055 #183)'],
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
    check_run_seeds('smoke',list(range(SMOKE[0],SMOKE[1]+1)),plan);check(plan['smoke_range'].startswith('12550001-12550006'),'plan smoke_range')
    T=target_ranges(plan);rep['cases_by_key']={k:T[k][1]-T[k][0]+1 for k in COUNTS};rep['total_cases']=sum(rep['cases_by_key'].values())
    ok=(not rep['pairwise_overlaps'] and not rep['prior_overlaps'] and rep['all_tokens_allowed'] and ts['files_scanned']>0 and ts['gz_files_decompressed']>0
        and all(x[3]=='refused' for x in neg) and rep['cases_by_key']==COUNTS and rep['total_cases']==12
        and 'BRUTE_PLAN_057.json' in rep['prior_files'] and 'BRUTE_PLAN_058.json' not in rep['prior_files'])
    rep['eps_by_key']=EPS_OF;rep['PASS']=ok;txt=json.dumps(rep,indent=1,default=list);print(txt[-900:])
    if '--write' in argv:
        p=ROOT/argv[argv.index('--write')+1];p.parent.mkdir(parents=True,exist_ok=True)
        with open(p,'x') as fh:fh.write(txt+'\n')
    if not ok:raise VerificationError('seed check failed')
    return 0


if __name__=='__main__':sys.exit(main(sys.argv[1:]))
