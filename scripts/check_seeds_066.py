"""Seed assertion for study-066 (BRUTE_PLAN_066 heldout_ranges: scale20 '12660101-12660106', scale24 '12660201-12660204';
smoke range 12660301-12660306 from the plan's smoke_range). Run and ledgered (seedcheck_066) AFTER build_authorization_066, BEFORE the
study tooling is committed and before any run code touches a fresh seed. New file (from check_seeds_065): the check_seeds_064 logic (rules J, K, L, M) with the
066 ranges, plus rule M generalised to this study (declared here, before the scan): a token in results/RESEARCH_LEDGER.jsonl is allowed
only if EVERY ledger line containing it is the preregistration_066 entry with source experiments/BRUTE_PLAN_066.json. The 063, 064 and 065 target
and smoke ranges are priors. Two target families (scale20, 6 seeds; scale24, 4 seeds); noise is drawn per reading.
Every tracked file is scanned, .gz archives decompressed.
Plan rule on a hit: the part moves by a ledgered deviation before any data.
  PYTHONPATH=. python scripts/check_seeds_066.py [--write results/diag-066/SEEDCHECK_066.json]
"""
import gzip,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check,load
from scripts.check_seeds_013 import int_pairs,_overlap
from scripts import check_seeds_045 as c45
from scripts import check_seeds_065 as c65
PLAN=ROOT/'experiments/BRUTE_PLAN_066.json'
EXTRA_PRIOR={**c65.EXTRA_PRIOR,'smoke_065':c65.SMOKE,**{'plan065/'+k:v for k,v in c65.ranges_065(load(ROOT/'experiments/BRUTE_PLAN_065.json')).items()}}
SMOKE=(12660301,12660306)
FAMILY_OF={'scale20':'scale20','scale24':'scale24'}
EPS_OF={'scale20':'0 (C20), 0.30 (S30, S30b; noise drawn per reading)','scale24':'0 (C24), 0.30 (S24; noise drawn per reading)'}
COUNTS={'scale20':6,'scale24':4}
TOKEN=re.compile(rb'(?<![0-9.eE\-])(1[12][0-9]{6})(?![0-9.eE])');ANY=re.compile(rb"1[12][0-9]{6}");span=c45.span
SELF=('BRUTE_PLAN_066','SEEDCHECK_066','check_seeds_066')


def prior_files():
    return [ROOT/'experiments/PLAN.json']+sorted(p for p in (ROOT/'experiments').glob('BRUTE_PLAN_0*.json')
                                                 if not p.name.startswith('BRUTE_PLAN_066') and 'FREEZE' not in p.name)


def prior_ranges():
    out={}
    for p in prior_files():
        for path,r in int_pairs(load(p)):out[p.name+path]=r
    out.update(EXTRA_PRIOR);return out


def target_ranges(plan=None):
    plan=plan or load(PLAN);H=plan['heldout_ranges'];return {k:span(H[k]) for k in FAMILY_OF}


def ranges_066(plan=None):
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


OWN=re.compile(r'^(experiments|scripts|tests)/[a-z0-9_]+_(066|0630)\.py$')


def rule_l(f,v,ranges):
    """Rule L (carried from 055 #183, declared here before any scan): a standalone token that lies in the 066 smoke range
    and in no 066 target range is allowed in this study's own tooling source (experiments|scripts|tests/*_066.py or *_0630.py),
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
    J=[c45.rule_j(f,v,ranges) for f,v in tok];K=[c45.rule_k(f,v) for f,v in tok];L=[rule_l(f,v,ranges) for f,v in tok];M=[rule_m(f,v,ranges) for f,v in tok]
    return {'files_scanned':scanned,'gz_files_decompressed':gz,'standalone_tokens_in_066_ranges':tok,'occurrences_any_in_066_ranges':emb,
            'standalone_11_12_prefix_token_count':block,'rule_j':J,'rule_k':K,'rule_l':L,'rule_m':M,
            'allowed':[j['allowed'] or k['allowed'] or l['allowed'] or m['allowed'] for j,k,l,m in zip(J,K,L,M)]}


NEGATIVE=(('target',12659001,None),('smoke',12659001,None),('target',12660301,None),('smoke',12660101,None),
          ('target',12660107,'scale20'),('target',12660100,'scale20'),('target',12660205,'scale24'),('target',12660200,'scale24'),
          ('target',12660201,'scale20'),('target',12660101,'scale24'),('target',12650101,None),('target',12650106,None),
          ('target',12640101,None),('smoke',12660307,None),('smoke',12660300,None),('smoke',12650301,None),('target',12670001,None))


LEDGER='results/RESEARCH_LEDGER.jsonl'


def rule_m(f,v,ranges):
    out={'file':f,'token':v,'lines':[],'allowed':False}
    if f!=LEDGER or not any(a<=v<=b for a,b in ranges.values()):return out
    ok=True
    for i,ln in enumerate((ROOT/f).read_text().splitlines(),1):
        if str(v) not in ln:continue
        e=json.loads(ln);good=e.get('event')=='preregistration_066' and e.get('source')=='experiments/BRUTE_PLAN_066.json'
        out['lines'].append([i,e.get('event'),good]);ok=ok and good
    out['allowed']=ok and bool(out['lines']);return out


def main(argv=()):
    argv=list(argv);plan=load(PLAN);new=ranges_066(plan);prior=prior_ranges()
    rep={'schema':'brute.seedcheck.v63','v0630_ranges':new,'prior_files':[p.name for p in prior_files()],'prior_range_count':len(prior),
         'rules_declared_before_scan':['J (cpu_jiffies, smoke only)','K (refused negative_controls probe in a SEEDCHECK file)',
                                   'L (066 smoke-range token in study-066 own tooling source; carried from 055 #183)','M (plan-066 preregistration ledger note; declared before the scan)'],
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
    check_run_seeds('smoke',list(range(SMOKE[0],SMOKE[1]+1)),plan);check(plan['smoke_range'].startswith('12660301-12660306'),'plan smoke_range')
    T=target_ranges(plan);rep['cases_by_key']={k:T[k][1]-T[k][0]+1 for k in COUNTS};rep['total_cases']=sum(rep['cases_by_key'].values())
    ok=(not rep['pairwise_overlaps'] and not rep['prior_overlaps'] and rep['all_tokens_allowed'] and ts['files_scanned']>0 and ts['gz_files_decompressed']>0
        and all(x[3]=='refused' for x in neg) and rep['cases_by_key']==COUNTS and rep['total_cases']==10
        and 'BRUTE_PLAN_065.json' in rep['prior_files'] and 'BRUTE_PLAN_066.json' not in rep['prior_files'])
    rep['eps_by_key']=EPS_OF;rep['PASS']=ok;txt=json.dumps(rep,indent=1,default=list);print(txt[-900:])
    if '--write' in argv:
        p=ROOT/argv[argv.index('--write')+1];p.parent.mkdir(parents=True,exist_ok=True)
        with open(p,'x') as fh:fh.write(txt+'\n')
    if not ok:raise VerificationError('seed check failed')
    return 0


if __name__=='__main__':sys.exit(main(sys.argv[1:]))
