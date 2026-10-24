"""Build a portable archive of exactly the tagged tree with git archive, after verification. No overwrite."""
import argparse,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import sha
from scripts.verify_release import verify


def pack(ref='v0.1.0',out_dir=ROOT.parent):
    target=Path(out_dir)/f'Brute-{ref}.zip'
    if target.exists():raise RuntimeError('refusing overwrite '+str(target))
    record=verify(fast=True)
    subprocess.run(['git','-C',str(ROOT),'archive','--format=zip',f'--prefix=Brute-{ref}/','-o',str(target),ref],check=True)
    return {'schema':'brute.package-check.v1','ref':ref,'archive':str(target),'sha256':sha(target),'bytes':target.stat().st_size,
            'verify':record['status']}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--ref',default='v0.1.0');print(json.dumps(pack(ap.parse_args().ref),indent=2))
