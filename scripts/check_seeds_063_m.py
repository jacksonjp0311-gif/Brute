"""Seed assertion for study-063, attempt 2 (deviation #200). New file. Attempt 1 (results/diag-063/SEEDCHECK_063_ATTEMPT1_FAIL.json,
published) found ONE standalone target token: results/RESEARCH_LEDGER.jsonl line 1261, the preregistration_063 entry, whose note
echoes the plan's own declared range (source experiments/BRUTE_PLAN_063.json). The plan file itself is excluded from the scan for
the same reason, so this is the plan's declaration, not a prior use of the seeds. No 063 seed has been run by any code.
This attempt runs check_seeds_063 unchanged (rules J, K, L, every check, every negative control) against the tracked tree at the
fixed commit ede7b9b (check_seeds_063 committed; nothing later), in a scratch git worktree, and adds ONE rule, declared here and
disclosed as a post-failure addition in deviation #200:
  Rule M: a token in results/RESEARCH_LEDGER.jsonl is allowed only if EVERY ledger line containing it (any occurrence) is the
  preregistration_063 entry with source experiments/BRUTE_PLAN_063.json and the token lies in a range that plan declares.
Every other token still needs J, K or L. M never allows a token in any other file or event.
  PYTHONPATH=. python scripts/check_seeds_063_m.py [--commit ede7b9b] --write results/diag-063/SEEDCHECK_063.json"""
import json,re,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts import check_seeds_063 as C
COMMIT='ede7b9b';LEDGER='results/RESEARCH_LEDGER.jsonl'


def rule_m(root,f,v,ranges):
    out={'file':f,'token':v,'lines':[],'allowed':False}
    if f!=LEDGER or not any(a<=v<=b for a,b in ranges.values()):return out
    ok=True
    for i,ln in enumerate((root/f).read_text().splitlines(),1):
        if str(v) not in ln:continue
        e=json.loads(ln);good=e.get('event')=='preregistration_063' and e.get('source')=='experiments/BRUTE_PLAN_063.json'
        out['lines'].append([i,e.get('event'),good]);ok=ok and good
    out['allowed']=ok and bool(out['lines']);return out


def main(argv=()):
    argv=list(argv);commit=argv[argv.index('--commit')+1] if '--commit' in argv else COMMIT
    out=ROOT/argv[argv.index('--write')+1] if '--write' in argv else None
    full=subprocess.run(['git','rev-parse',commit],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
    tree=Path(tempfile.mkdtemp(prefix='seedtree063-',dir='/tmp'))/'t'
    subprocess.run(['git','worktree','add','--detach',str(tree),full],cwd=ROOT,check=True,capture_output=True)
    tmp=tree.parent/'rep.json';err=None;base=C.token_scan
    def scan(ranges):
        ts=base(ranges);toks=[[j['file'],j['token']] for j in ts['rule_j']]
        ts['rule_m']=[rule_m(tree,f,v,ranges) for f,v in toks]
        ts['allowed']=[a or m['allowed'] for a,m in zip(ts['allowed'],ts['rule_m'])];return ts
    try:
        C.ROOT=tree;C.token_scan=scan
        try:C.main(['--write',str(tmp)])
        except C.VerificationError as e:err=str(e)
        rep=json.loads(tmp.read_text())
    finally:
        C.token_scan=base
        subprocess.run(['git','worktree','remove','--force',str(tree)],cwd=ROOT,check=True,capture_output=True)
    rep={'scanned_commit':full,'attempt':2,'deviation':'#200','rule_m_declared':'M (plan-063 preregistration ledger note echoing its own range)',**rep}
    txt=json.dumps(rep,indent=1,default=list)
    if out is not None:
        out.parent.mkdir(parents=True,exist_ok=True)
        with open(out,'x') as fh:fh.write(txt+'\n')
    print('PASS' if rep['PASS'] else 'FAIL',full,err or '')
    return 0 if rep['PASS'] else 1


if __name__=='__main__':sys.exit(main(sys.argv[1:]))
