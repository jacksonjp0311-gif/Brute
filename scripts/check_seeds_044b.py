"""Adjudication of the seedcheck_044 failure (deviation #161 item 2). New file; SEEDCHECK_044.json is not edited.
Written AFTER the seedcheck_044 scan. The plan 044 note asks that an adjudication rule be declared before the scan; that held for
rule J (cpu_jiffies) only. This rule is post-scan and is published as such (#161 item 2); it is narrow and mechanical.

SEEDCHECK_044 failed only because rule J did not cover one standalone token in a target range: 10930001 (lowobs12) at
results/diag-043/SEEDCHECK_043.json. This check passes iff:
  1. every other SEEDCHECK_044 clause holds as recorded (no pairwise or prior overlaps, all negative controls refused, counts
     12/6 = 18, eps 0, prior files include BRUTE_PLAN_043.json, files scanned > 0);
  2. the listed in-range tokens equal the declared set exactly;
  3. parsing each listed file as one JSON document, every key path holding the value is ('negative_controls', i, 1) where item i
     records the verdict 'refused' (a range-membership probe of scripts/check_seeds_043.check_run_seeds, which compares
     integers and never builds a world from them);
  4. the git blob of scripts/check_seeds_043.py (the probe code that produced the item) resolves and is recorded.
  PYTHONPATH=. python scripts/check_seeds_044b.py [--write results/diag-044/SEEDCHECK_044B.json]
"""
import json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError
from scripts.check_seeds_043b import _walk
SRC=ROOT/'results/diag-044/SEEDCHECK_044.json'
DECLARED=[['results/diag-043/SEEDCHECK_043.json',10930001]]
PROBE_FILE='scripts/check_seeds_043.py'


def paths_in(doc,tok):
    out=[];_walk(doc,tok,(),out);return out


def is_probe(doc,p):
    return len(p)==3 and p[0]=='negative_controls' and p[2]==1 and doc['negative_controls'][p[1]][-1]=='refused'


def blob(rel):
    return subprocess.run(['git','rev-parse','HEAD:'+rel],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()


def main(argv=()):
    argv=list(argv);s=json.loads(SRC.read_text());ts=s['token_scan']
    c1=(not s['pairwise_overlaps'] and not s['prior_overlaps'] and ts['files_scanned']>0
        and all(x[3]=='refused' for x in s['negative_controls']) and s['cases_by_key']=={'lowobs12':12,'control':6}
        and s['total_cases']==18 and set(s['eps_by_key'].values())=={0.0} and 'BRUTE_PLAN_043.json' in s['prior_files'])
    listed=ts['standalone_tokens_in_044_ranges'];c2=sorted(map(list,listed))==sorted(DECLARED)
    hits=[];c3=bool(listed)
    for f,tok in listed:
        doc=json.loads((ROOT/f).read_text());ps=paths_in(doc,tok)
        ok=bool(ps) and all(is_probe(doc,p) for p in ps);c3=c3 and ok
        hits.append({'file':f,'token':tok,'paths':[list(p) for p in ps],'items':[doc['negative_controls'][p[1]] for p in ps if p[0]=='negative_controls'],'allowed':ok})
    b=blob(PROBE_FILE)
    rep={'schema':'brute.seedcheck_b.v41','source':str(SRC.relative_to(ROOT)),'declared':DECLARED,'written':'after the seedcheck_044 scan (post-scan rule; #161 item 2)',
         'clause_1_other_clauses':c1,'clause_2_listed_equals_declared':c2,'clause_3_only_refused_probe_items':c3,
         'clause_4_probe_file_blob':b,'hits':hits,'PASS':bool(c1 and c2 and c3 and b)}
    txt=json.dumps(rep,indent=1);print(txt)
    if '--write' in argv:
        p=ROOT/argv[argv.index('--write')+1]
        with open(p,'x') as fh:fh.write(txt+'\n')
    if not rep['PASS']:raise VerificationError('seedcheck_044b failed')
    return 0


if __name__=='__main__':sys.exit(main(sys.argv[1:]))
