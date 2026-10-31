"""Adjudication of the seedcheck_043 failure (deviation 159 item 1). New file; SEEDCHECK_043.json is not edited.

SEEDCHECK_043 failed only on clause 4/erratum: one standalone token in a 043 range, 10980005 (the SMOKE range), at
results/study-023/HB_SENTINEL_023.jsonl. This check passes iff:
  1. every other SEEDCHECK_043 clause holds as recorded (no pairwise or prior overlaps, all negative controls refused,
     counts 12/12/6 = 30, eps 0, prior files include BRUTE_PLAN_042.json);
  2. every listed in-range token lies only in the smoke range, never in a target range;
  3. re-reading each listed file, every line containing the token parses as JSON and every JSON key path holding the
     value is under a 'cpu_jiffies' object (a CPU counter, not a seed);
  4. the listed set equals the declared erratum exactly.
  PYTHONPATH=. python scripts/check_seeds_043b.py [--write results/diag-043/SEEDCHECK_043B.json]
"""
import gzip,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError
SRC=ROOT/'results/diag-043/SEEDCHECK_043.json'
DECLARED=[['results/study-023/HB_SENTINEL_023.jsonl',10980005]]


def _walk(o,tok,path,out):
    if isinstance(o,dict):
        for k,v in o.items():_walk(v,tok,path+(k,),out)
    elif isinstance(o,list):
        for i,v in enumerate(o):_walk(v,tok,path+(i,),out)
    elif type(o) is int and o==tok:out.append(path)


def paths_of(line,token):
    out=[];_walk(json.loads(line),token,(),out);return out


def allowed(paths):
    return bool(paths) and all('cpu_jiffies' in p[:-1] for p in paths)


def _lines(p):
    op=gzip.open if p.suffix=='.gz' else open
    with op(p,'rt') as f:
        for i,l in enumerate(f,1):yield i,l


def main(argv=None):
    a=list(sys.argv[1:] if argv is None else argv);out=a[a.index('--write')+1] if '--write' in a else None
    raw=SRC.read_bytes();d=json.loads(raw);rng=d['v0400_ranges']
    clauses={'schema':d['schema']=='brute.seedcheck.v40','pairwise_overlaps_empty':d['pairwise_overlaps']==[],
             'prior_overlaps_empty':d['prior_overlaps']==[],
             'negatives_refused':all(n[-1]=='refused' for n in d['negative_controls']) and len(d['negative_controls'])>0,
             'counts':d['cases_by_key']=={'lowobs12':12,'scale16_rep':12,'control':6} and d['total_cases']==30,
             'eps0':all(v==0.0 for v in d['eps_by_key'].values()),
             'prior_042':any(str(f).endswith('BRUTE_PLAN_042.json') for f in d['prior_files']),
             'only_failure_is_erratum':d['erratum_1']['all_outside_043_ranges'] is False and d['erratum_1']['known_listed'] is True}
    listed=d['token_scan']['standalone_tokens_in_043_ranges'];occ=[]
    for f,tok in listed:
        in_t=[k for k,(lo,hi) in rng.items() if lo<=tok<=hi]
        hits=[]
        for i,l in _lines(ROOT/f):
            if str(tok) in l:
                ps=paths_of(l,tok);hits.append({'line':i,'paths':[list(p) for p in ps],'allowed':allowed(ps)})
        occ.append({'file':f,'token':tok,'ranges':in_t,'smoke_only':in_t==['smoke'],'hits':hits,
                    'all_allowed':bool(hits) and all(h['allowed'] for h in hits)})
    clauses['smoke_only']=all(o['smoke_only'] for o in occ)
    clauses['all_cpu_jiffies']=all(o['all_allowed'] for o in occ)
    clauses['equals_declared']=sorted(map(list,listed))==sorted(DECLARED)
    ok=all(clauses.values())
    rep={'schema':'brute.seedcheck043b.v40','source':str(SRC.relative_to(ROOT)),'source_sha256':hashlib.sha256(raw).hexdigest(),
         'declared_erratum':DECLARED,'clauses':clauses,'occurrences':occ,'PASS':ok}
    print(json.dumps(rep,indent=1))
    if out:Path(out).write_text(json.dumps(rep,indent=1,sort_keys=True)+'\n')
    if not ok:raise VerificationError('seedcheck_043b failed')
    return rep


if __name__=='__main__':main()
