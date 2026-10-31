"""Seed assertion for study-045 (BRUTE_PLAN_045 heldout_ranges: scale16 '11130001-11130012', control '11190001-11190006', each a
string 'a-b'; smoke range 11290001-11290006 from the plan's smoke_range). Run and ledgered (seedcheck_045) AFTER
build_authorization_045 and BEFORE any v0.42.0 run code touches a target seed. New file (check_seeds_044 logic, frozen, with the
045 ranges parsed from strings and the 044 ranges and 044 smoke range as priors; every case eps 0).

Adjudication rules, BOTH written into this file BEFORE the scan (the 044 lesson: rule K was post-scan in 044b, now declared):
  rule J: a standalone in-range token is ALLOWED iff it lies only in the smoke range (never a target range) and every JSON key
     path holding it, on every line of the file that contains it, is under a 'cpu_jiffies' object (check_seeds_043b.allowed);
  rule K: a standalone in-range token is ALLOWED iff the file is a tracked results/diag-0*/SEEDCHECK_0*.json document and,
     parsing it as one JSON document, every key path holding the value is ('negative_controls', i, 1) where item i records the
     verdict 'refused' (a range-membership probe; integers compared, no world ever built from them; the check_seeds_044b rule).
  Every in-range token is listed either way; a target-range token allowed by neither rule fails the check. Plan rule on a hit:
  the range moves to the next unused odd prefix (1121, 1129), declared in the pre-run deviation.

Asserts (exit 0 iff all hold):
  1. the 045 ranges (2 targets + smoke) parse as consecutive integer spans and are pairwise disjoint;
  2. disjoint from every [lo, hi] pair in experiments/PLAN.json and every experiments/BRUTE_PLAN_0*.json except
     BRUTE_PLAN_045* (parsed), plus all earlier extras, the 044 smoke range and the 044 target ranges;
  3. token scan of every git-tracked file under results/ or experiments/ (incl. .gz; BRUTE_PLAN_045* and SEEDCHECK_045*
     excluded): every standalone token in a 045 range is allowed by rule J or rule K;
  4. check_run_seeds refuses any seed outside its declared range (negative controls);
  5. 12 + 6 = 18 target seeds -> 18 fresh cases; eps 0 everywhere.
  PYTHONPATH=. python scripts/check_seeds_045.py [--write results/diag-045/SEEDCHECK_045.json]
"""
import gzip,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check,load
from scripts.check_seeds_013 import int_pairs,_overlap
from scripts import check_seeds_033 as c33
from scripts import check_seeds_044 as c44
from scripts.check_seeds_043b import paths_of,allowed,_walk
PLAN=ROOT/'experiments/BRUTE_PLAN_045.json'
EXTRA_PRIOR={**c44.EXTRA_PRIOR,'smoke_044':c44.SMOKE,**{'plan044/'+k:v for k,v in c44.ranges_044().items()}}
SMOKE=(11290001,11290006)
FAMILY_OF={'scale16':'scale16','control':'control_cycle3'}
EPS_OF={k:0.0 for k in FAMILY_OF}
COUNTS={'scale16':12,'control':6}
TOKEN=re.compile(rb'(?<![0-9.eE\-])(11[0-9]{6})(?![0-9.eE])');ANY=re.compile(rb"11[0-9]{6}")
SCAN_SUFFIX=c33.SCAN_SUFFIX
SEEDCHECK_FILE=re.compile(r'^results/diag-0[0-9]+/SEEDCHECK_0[0-9A-Za-z_]*\.json$')


def span(s):
    a,b=(int(x) for x in str(s).split('-'));check(a<=b,f'bad range {s}');return (a,b)


def prior_files():
    return [ROOT/'experiments/PLAN.json']+sorted(p for p in (ROOT/'experiments').glob('BRUTE_PLAN_0*.json')
                                                 if not p.name.startswith('BRUTE_PLAN_045') and 'FREEZE' not in p.name)


def prior_ranges():
    out={}
    for p in prior_files():
        for path,r in int_pairs(load(p)):out[p.name+path]=r
    out.update(EXTRA_PRIOR);return out


def target_ranges(plan=None):
    plan=plan or load(PLAN);H=plan['heldout_ranges'];return {k:span(H[k]) for k in FAMILY_OF}


def ranges_045(plan=None):
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


def _lines(p):
    op=gzip.open if p.suffix=='.gz' else open
    with op(p,'rt',errors='replace') as f:
        for i,l in enumerate(f,1):yield i,l


def rule_j(f,tok,ranges):
    in_r=[k for k,(lo,hi) in ranges.items() if lo<=tok<=hi];hits=[]
    for i,l in _lines(ROOT/f):
        if str(tok) in l:
            try:ps=paths_of(l,tok)
            except ValueError:ps=[]
            hits.append({'line':i,'paths':[list(p) for p in ps],'allowed':allowed(ps)})
    return {'file':f,'token':tok,'ranges':in_r,'smoke_only':in_r==['smoke'],'hits':hits,
            'allowed':in_r==['smoke'] and bool(hits) and all(h['allowed'] for h in hits)}


def rule_k(f,tok):
    if not SEEDCHECK_FILE.match(f):return {'file':f,'token':tok,'seedcheck_file':False,'paths':[],'allowed':False}
    try:doc=json.loads((ROOT/f).read_text())
    except ValueError:return {'file':f,'token':tok,'seedcheck_file':True,'parse':False,'paths':[],'allowed':False}
    ps=[];_walk(doc,tok,(),ps)
    nc=doc.get('negative_controls') if isinstance(doc,dict) else None
    probe=lambda p:(len(p)==3 and p[0]=='negative_controls' and p[2]==1 and isinstance(nc,list) and nc[p[1]][-1]=='refused')
    return {'file':f,'token':tok,'seedcheck_file':True,'paths':[list(p) for p in ps],'allowed':bool(ps) and all(probe(p) for p in ps)}


def token_scan(ranges):
    files=subprocess.run(['git','ls-files','results','experiments'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.split()
    files=[f for f in files if f.endswith(SCAN_SUFFIX) and not Path(f).name.startswith('BRUTE_PLAN_045') and 'SEEDCHECK_045' not in f]
    inr=lambda v:any(a<=v<=b for a,b in ranges.values());tok=[];emb=0;scanned=0;block=0
    for f in files:
        p=ROOT/f
        if not p.exists():continue
        b=gzip.open(p).read() if f.endswith('.gz') else p.read_bytes();scanned+=1
        for m in TOKEN.finditer(b):
            v=int(m.group(1));block+=1
            if inr(v) and [f,v] not in tok:tok.append([f,v])
        emb+=sum(1 for m in ANY.finditer(b) if inr(int(m.group(0))))
    J=[rule_j(f,v,ranges) for f,v in tok];K=[rule_k(f,v) for f,v in tok]
    return {'files_scanned':scanned,'standalone_tokens_in_045_ranges':tok,'occurrences_any_in_045_ranges':emb,
            'standalone_11_prefix_token_count':block,'rule_j':J,'rule_k':K,'allowed':[j['allowed'] or k['allowed'] for j,k in zip(J,K)]}


NEGATIVE=(('target',11299001,None),('smoke',11299001,None),('target',11290001,None),('smoke',11130001,None),
          ('target',11130013,'scale16'),('target',11190001,'scale16'),('target',11190007,'control'),('target',11130001,'control'),
          ('target',10930001,None),('target',10970001,None),('target',10990001,None),('target',11210001,None),
          ('smoke',11290007,None),('smoke',11289999,None),('target',11129999,None),('target',11140001,None))


def main(argv=()):
    argv=list(argv);plan=load(PLAN);new=ranges_045(plan);prior=prior_ranges()
    rep={'schema':'brute.seedcheck.v42','v0420_ranges':new,'prior_files':[p.name for p in prior_files()],'prior_range_count':len(prior),
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
    check_run_seeds('smoke',list(range(SMOKE[0],SMOKE[1]+1)),plan);check(plan['smoke_range'].startswith('11290001-11290006'),'plan smoke_range')
    T=target_ranges(plan);rep['cases_by_key']={k:T[k][1]-T[k][0]+1 for k in COUNTS};rep['total_cases']=sum(rep['cases_by_key'].values())
    ok=(not rep['pairwise_overlaps'] and not rep['prior_overlaps'] and rep['all_tokens_allowed'] and ts['files_scanned']>0
        and all(x[3]=='refused' for x in neg) and rep['cases_by_key']==COUNTS and rep['total_cases']==18==plan['cases']['total_fresh']
        and 'BRUTE_PLAN_044.json' in rep['prior_files'] and 'BRUTE_PLAN_045.json' not in rep['prior_files'])
    rep['eps_by_key']=EPS_OF;rep['PASS']=ok;txt=json.dumps(rep,indent=1,default=list);print(txt[-1500:])
    if '--write' in argv:
        p=ROOT/argv[argv.index('--write')+1];p.parent.mkdir(parents=True,exist_ok=True)
        with open(p,'x') as fh:fh.write(txt+'\n')
    if not ok:raise VerificationError('seed check failed')
    return 0


if __name__=='__main__':sys.exit(main(sys.argv[1:]))
