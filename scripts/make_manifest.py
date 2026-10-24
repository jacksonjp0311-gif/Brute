"""Regenerate MANIFEST.sha256 from the git-tracked file list (or the tree when there is no .git)."""
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import sha
SKIP=('__pycache__','.pytest_cache','runs','.git')


def tracked(root=ROOT):
    root=Path(root)
    if (root/'.git').exists():
        out=subprocess.run(['git','-C',str(root),'ls-files','-z'],capture_output=True,check=True).stdout.decode()
        rels=[r for r in out.split('\0') if r]
    else:
        rels=[p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()
              and not any(s in SKIP for s in p.relative_to(root).parts) and not p.name.endswith('.pyc')]
    return sorted(r for r in rels if r!='MANIFEST.sha256' and (root/r).is_file())


def build(root=ROOT):
    return ''.join(f'{sha(Path(root)/r)}  {r}\n' for r in tracked(root))


if __name__=='__main__':
    (ROOT/'MANIFEST.sha256').write_text(build());print(len(tracked()),'files in MANIFEST.sha256')
