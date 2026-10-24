"""Read-only figures and browser data derived from the sealed research study."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RESULT=ROOT/'results/study-001/RESULTS.json'

def run():
    original=json.loads(RESULT.read_text())
    files=original['cases'];examples=[]
    for family in original['plan']['heldout_ranges']:
        for rate in original['plan']['mask_rates']:
            selected=next(x for x in files if x['family']==family and x['mask_rate']==rate)
            examples.append({'family':family,'rate':rate,'seed':selected['seed'],'trace':selected['trace'],
                 'initial':selected['initial_visible'],'expanded_status':selected['expanded_status'],
                 'legacy_wrong':selected['legacy_false_certifications'],
                 'expanded_wrong':selected['conditional_false_certifications'],
                 'conditional':selected['conditional_certificates'],
                 'public':selected['public_certificates']})
    data={'schema':'bgr90.readonly-viewer.v1','study':original['plan']['study'],'source_sha256':hashlib.sha256(RESULT.read_bytes()).hexdigest(),
          'disclaimer':'Actual masked observations and evaluator-held true emissions. Probabilities and supports are model-conditional; all public certificate claims absent.',
          'examples':examples}
    (ROOT/'ui/data.js').write_text('window.BGR90_DATA='+json.dumps(data,sort_keys=True,separators=(',',':'))+';\n')
    print('viewer',len(examples),'real recorded steps',sum(len(x['trace']) for x in examples))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    sums=original['summary'];name=list(original['plan']['heldout_ranges'])
    old=[sums[k]['legacy_wrong_conditional_certs'] for k in name];new=[sums[k]['expanded_wrong_conditional_certs'] for k in name]
    import numpy as np
    x=np.arange(len(name))
    fig,ax=plt.subplots(figsize=(11,4.8))
    ax.bar(x-.18,old,.35,label='Legacy n≤3 conditional errors')
    ax.bar(x+.18,new,.35,label='New n≤4 conditional errors')
    ax.set_xticks(x,name,rotation=28,ha='right');ax.set_ylabel('Incorrect conditional certificates')
    ax.set_title('BGR v0.90 · Conditional certainty is only as sound as its grammar')
    ax.legend();ax.grid(axis='y',alpha=.23);fig.tight_layout()
    fig.savefig(ROOT/'assets/BGR-v0.90.0-conditional-errors.png',dpi=155);plt.close(fig)
    fig,ax=plt.subplots(figsize=(11,4.8))
    ax.bar(name,[sums[k]['expanded_conditional_certs'] for k in name])
    ax.set_xticklabels(name,rotation=28,ha='right');ax.set_ylabel('Model-conditional unanimity certificates')
    ax.set_title('BGR v0.90 · Exact n≤4 support, verified only within bounded model grammar')
    ax.grid(axis='y',alpha=.23);fig.tight_layout()
    fig.savefig(ROOT/'assets/BGR-v0.90.0-certification-coverage.png',dpi=155);plt.close(fig)
    print('source-derived scientific plots complete')

if __name__=='__main__':run()
