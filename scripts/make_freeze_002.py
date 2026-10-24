"""Regenerate experiments/BRUTE_SOURCE_FREEZE_002.json (study-002 source lock).

Study-001's experiments/SOURCE_FREEZE.json is never touched.
"""
import json
from pathlib import Path
from experiments.brute_common import ROOT,FREEZE,sha
FILES=sorted([*(p.relative_to(ROOT).as_posix() for d in ('brute/core','bgr89','bgr90') for p in (ROOT/d).glob('*.py')),
    'brute/__init__.py','brute/evaluation.py','experiments/__init__.py','experiments/BRUTE_PLAN_002.json',
    'experiments/brute_common.py','experiments/brute_calibrate.py','experiments/brute_study.py',
    'experiments/brute_audit.py','experiments/v90_independent_reference.py','tests/test_brute_abstention.py'])


def build():
    return {'schema':'brute.source-freeze.v1','study':'BRUTE-010-ABSTENTION-002','status':'frozen',
            'sha256_files':{rel:sha(ROOT/rel) for rel in FILES}}


if __name__=='__main__':
    FREEZE.write_text(json.dumps(build(),sort_keys=True,indent=2)+'\n');print(len(FILES),'files frozen')
