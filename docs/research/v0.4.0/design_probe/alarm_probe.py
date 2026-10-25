"""Alarm recalibration feasibility on design data (sealed study-004 P and study-005 P3 passive traces)."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
INF=('cycle3','switch3','unstructured3','unaliased2','ood4')
rows=[]
for st,arm in (('004','P'),('005','P3')):
    R=json.load(open(ROOT/f'results/study-{st}/RESULTS.json'))
    for c in R['cases']:
        res=[r['residual_after'] for r in c['arms'][arm]['trace'] if r['residual_after'] is not None]
        rows.append((st,c['family'],c['seed'],c['mask_rate'],max(res),res))
out={}
for fam in INF+('ood5','drift4'):
    mx=sorted(r[4] for r in rows if r[1]==fam)
    out[fam]={'n':len(mx),'max':mx[-1],'q99':mx[int(.99*len(mx))-1],'q95':mx[int(.95*len(mx))-1]}
inmax=sorted(r[4] for r in rows if r[1] in INF)
for tau in (1.433141502274,1.6,1.8,2.0,2.2,2.5):
    out[f'tau={tau}']={f:sum(r[4]>tau for r in rows if r[1]==f)/sum(1 for r in rows if r[1]==f) for f in INF+('ood5','drift4')}
# resume rule: alarm clears after W=8 consecutive residual<=tau; count in-family cases still alarmed at the end
for tau in (1.433141502274,):
    still=0;tot=0
    for r in rows:
        if r[1] not in INF:continue
        tot+=1;al=False;run=0
        for x in r[5]:
            if not al and x>tau:al=True;run=0
            elif al:
                run=run+1 if x<=tau else 0
                if run>=8:al=False
        still+=al
    out['resume_W8_in_family_end_alarmed_frac']=still/tot
print(json.dumps(out,indent=1))
json.dump(out,open(Path(__file__).parent/'outputs/alarm_probe.json','w'),indent=1)
