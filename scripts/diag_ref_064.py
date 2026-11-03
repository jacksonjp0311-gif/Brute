"""Exploratory diagnostic for plan 064 (run BEFORE the plan is locked; NOT a study, never gated): does the clique-pinned
reference (experiments/v0610_reference.py) finish the GS_ref audit that the plain-CNF reference could not (study-063: 2 of 7
decided audited in 1800 s), and does it agree with the frozen reference on the 2 records the frozen one did audit?
Runs the frozen study-063 reference machinery (scripts/run_reference_063.py -> run_reference_047 / run_reference_041) unchanged
except that run_reference_041._nmin and run_reference_041.exists_different are swapped for the pinned versions, with each
record's final_clique as a verified hint. Input: a COPY of the sealed results/study-063/main/RESULTS.json in a scratch dir (the
released study dir is never written). Output: results/diag-064/REF_PIN_DIAG_064.json (refuses overwrite). Observed.
  PYTHONPATH=. python scripts/diag_ref_064.py <scratch dir holding RESULTS.json> [--workers 4] [--budget 1800]"""
import json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,sha
from experiments import v0610_reference as PIN
from scripts import run_reference_063 as R63
from scripts import run_reference_047 as R47
from scripts import run_reference_041 as R41
OUT=ROOT/'results/diag-064/REF_PIN_DIAG_064.json'
_CUR={'C':None,'src':None}
_view63=R63.view;_audit63=R63._audit


def view(c,arm):
    r=_view63(c,arm);r['final_clique']=list(c['arms'][arm].get('final_clique') or []);return r


def _clique(acts,codes):
    if _CUR['C'] is None:_CUR['C'],_CUR['src']=PIN.verified_clique(acts,codes,_CUR['hint'])
    return _CUR['C']


def _nmin(acts,codes,k,N):return PIN.nmin(acts,codes,k,R41.M,N,_clique(acts,codes))


def _exd(acts,codes,n,k,m,M1,s1,mode,L):return PIN.exists_different(acts,codes,n,k,m,M1,s1,mode,L,_clique(acts,codes))


def _audit(r):
    _CUR.update(C=None,src=None,hint=r.get('final_clique') or None);x,cache,wall=_audit63(r)
    x['clique_used']=len(_CUR['C'] or []);x['clique_source']=_CUR['src'];return x,cache,wall


R41._nmin=_nmin;R41.exists_different=_exd;R47.view=view;R47._audit=_audit


def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv);d=Path(argv[0])
    if OUT.exists():raise SystemExit('refusing overwrite '+str(OUT))
    rc=R47.main(argv+['--output-name','REF_PIN_DIAG_064.json'])
    out=load(d/'REF_PIN_DIAG_064.json');old=load(ROOT/'results/study-063/main/REFERENCE_063.json')
    oldrec={x['id']:x for x in old['per_record'] if x.get('audited')}
    agree={i:{'old_label':o.get('label'),'new_label':next((x.get('label') for x in out['per_record'] if x['id']==i),None),
              'old_mismatches':o['mismatches'],'new_mismatches':next((x['mismatches'] for x in out['per_record'] if x['id']==i),None)} for i,o in oldrec.items()}
    out.update(schema='brute.diag.refpin.v61_0',label='Observed',purpose='exploratory diagnostic for plan 064; not evidence for any gate',
               input_sha256_matches_sealed=sha(d/'RESULTS.json')==sha(ROOT/'results/study-063/main/RESULTS.json'),agreement_with_frozen_reference=agree,
               script_sha256=sha(Path(__file__)))
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,indent=1,sort_keys=True)+'\n');return rc


if __name__=='__main__':sys.exit(main())
