"""Pre-run tooling-order check for study-024 (BRUTE_PLAN_024 GTI "release tooling after run_end", fix for #107): before launch, assert that no
release tooling (tests/test_release_0210*.py, scripts/verify_release_0210*.py, scripts/make_release_freeze_0210*.py) exists
in the tree or in git history of HEAD, and that the source freeze is valid. Exit 0 = ok; prints JSON."""
import glob,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
GLOBS=('tests/test_release_0210*.py','scripts/verify_release_0210*.py','scripts/make_release_freeze_0210*.py')


def check(root=ROOT):
    tree=sorted(str(Path(p).relative_to(root)) for g in GLOBS for p in glob.glob(str(root/g)))
    tracked=subprocess.run(['git','ls-files',*GLOBS],cwd=root,capture_output=True,text=True).stdout.split()
    return {'tree':tree,'tracked':tracked,'ok':not tree and not tracked}


if __name__=='__main__':
    r=check()
    if '--no-freeze' not in sys.argv:
        from experiments.brute_common_024 import check_freeze
        check_freeze();r['freeze_ok']=True
    print(json.dumps(r));sys.exit(0 if r['ok'] else 1)
