import json
from .explore import run
if __name__=='__main__':
    r=run(90211,'logic','lookahead',steps=40)
    print(json.dumps({k:r[k] for k in ('seed','family','policy','steps','identified','certified','incorrect')},indent=2))
