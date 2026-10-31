"""G_recount for study-049 (BRUTE_PLAN_049; pre-run deviation #171). New file. The per-case logic is the frozen
scripts/recount_047.py recount_case, imported unchanged, with its module ORDER / DELTA names bound in this process to the 049 arms
(API16E, API16E_b, API16E_c1; every arm at bound N = the family size). Parts r and c (block 'r' / 'c') are certify/16e runs on
sealed 048 traces; each is recounted, then compared independently with the sealed 048 API16D record (sha-checked against its
SEAL): label, n_min, canonical model, T_final, executed words, the 047 difference class, and (part c) canon16d byte for byte,
all recomputed here and checked against the stored comparison.
GR49_sound contradiction rule (#171): a part-r record contradicts its sealed record if (i) both are ID / IDF and the canonical
models differ, or (ii) the sealed record is AMB (two consistent rivals at its last round T) and the part-r record is ID / IDF on
an executed trace that is a prefix of the sealed trace up to T.
Writes <study>/RECOUNT_049.json (refuses overwrite).
  PYTHONPATH=. python scripts/recount_049.py results/study-049/main"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,write_new,sha
from scripts import recount_047 as R47
from scripts.recount_033 import canon
ORDER=('API16E','API16E_b','API16E_c1');CLASSES=('none','cap-timing','word-divergence','infidelity')
R47.ORDER=ORDER;R47.DELTA={a:None for a in ORDER}
recount_case=R47.recount_case;_counts=R47._counts
SEALED=ROOT/'results/study-048/main';PART_ARM={'r':'API16E','c':'API16E_c1'}


def sealed048():
    from scripts.study048_storage import ensure_raw
    ensure_raw();seal=load(SEALED/'SEAL.json')
    if sha(SEALED/'RESULTS.json')!=seal['results_sha256']:raise SystemExit('sealed 048 RESULTS changed')
    return {(c['key'],c['seed']):c for c in load(SEALED/'RESULTS.json')['cases'] if c['block']=='main'}


def _acts(c,a):
    from experiments import worlds_047 as W
    w=W.world(c['seed'],c['family']);return list(W.actions(c['seed'],0.0,w.k))+list(a['extra_acts'])


def replay_check(c,rec,S,arm):
    from experiments.brute_study_047 import canon16d
    s=S[(c['key'],c['seed'])];sa=s['arms']['API16D'];a=c['arms'][arm];bad=[]
    cm=lambda m:None if m is None else canon(m[0],m[1],0)
    x={'label':[rec['label'],sa['label']],'n_min':[a['n_min'],sa['n_min']],'canonical_model_equal':cm(a['model'])==cm(sa['model']),
       'T_final':[rec['T_final'],sa['T_final']]}
    x['same']=bool(x['label'][0]==x['label'][1] and x['n_min'][0]==x['n_min'][1] and x['canonical_model_equal'])
    x['same_step']=bool(x['same'] and x['T_final'][0]==x['T_final'][1])
    wa=[r['word'] for r in a['rounds'] if r.get('word')];ws=[r['word'] for r in sa['rounds'] if r.get('word')];x['words_equal']=wa==ws
    ca=sum(r['capped'] for r in a['rounds'])>0;cs=sum(r['capped'] for r in sa['rounds'])>0
    x['class']='none' if (x['same'] and x['words_equal']) else ('infidelity' if not ca and not cs else ('cap-timing' if x['words_equal'] else 'word-divergence'))
    x['sealed_capped_any']=cs;x['replay_capped_any']=ca;x['canon16d_equal']=canon16d(a)==canon16d(sa)
    dec=('ID','IDF');con=False
    if rec['label'] in dec and sa['label'] in dec and not x['canonical_model_equal']:con=True
    if rec['label'] in dec and sa['label']=='AMB':
        Ts=max(r['T'] for r in sa['rounds'] if r.get('M2') is not None);ra=_acts(c,a);sa_=_acts(s,sa)
        if len(ra)<=Ts and ra==sa_[:len(ra)]:con=True
    x['contradiction']=con;x['gain']=bool(rec['label'] in dec and sa['label']=='IDU')
    st=c.get('replay') or {}
    for k in ('label','n_min','canonical_model_equal','T_final','same','same_step','words_equal','class','sealed_capped_any','replay_capped_any','canon16d_equal'):
        if st.get(k)!=x[k]:bad.append(('replay',k,st.get(k),x[k]))
    if c.get('source')!='048' or list(c['arms'])!=[arm]:bad.append(('replay_source_or_arm',c.get('source'),list(c['arms'])))
    return x,bad


def _psum(rpc,p):
    v=[x for k,x in rpc.items() if k.startswith(p+'/')]
    return {'n':len(v),'same':sum(x['same'] for x in v),'canon16d_equal':sum(x['canon16d_equal'] for x in v),
            'contradictions':sum(x['contradiction'] for x in v),'gain':sum(x['gain'] for x in v),
            'gain_by_key':{k:sum(x['gain'] for kk,x in rpc.items() if kk.startswith(f'{p}/{k}/')) for k in ('scale16','control','scale20')},
            'classes':{q:sum(x['class']==q for x in v) for q in CLASSES}}


def main(argv=None):
    argv=sys.argv[1:] if argv is None else argv;d=Path(argv[0]);res=load(d/'RESULTS.json');per={};bad={};rp={};rpc={}
    S=sealed048() if res['replays'] else {}
    for c in res['replays']:
        p=c['block'];arm=PART_ARM[p];k=f"{p}/{c['key']}/{c['seed']}";rp[k],b=recount_case(c)
        x,b2=replay_check(c,rp[k][arm],S,arm);rpc[k]=x;b=b+b2
        if b:bad[k]=b
    for c in res['cases']:
        k=f"{c['block']}/{c['key']}/{c['seed']}";per[k],b=recount_case(c)
        if b:bad[k]=b
    main_=[v for k,v in per.items() if k.startswith('main/')];allv=list(per.values())+list(rp.values())
    sub=lambda p:{arm:_counts([v for k,v in per.items() if k.startswith(p)],arm) for arm in ('API16E','API16E_b')}
    rsub=lambda p,arm:_counts([v for k,v in rp.items() if k.startswith(p)],arm)
    out={'schema':'brute.recount.v46_0','results_sha256':sha(d/'RESULTS.json'),'replays':len(rp),'cases':len(per),
         'labels_main':{arm:_counts(main_,arm) for arm in ('API16E','API16E_b')},
         'labels_scale16_main':sub('main/scale16/'),'labels_control_main':sub('main/control/'),'labels_scale20_main':sub('main/scale20/'),
         'labels_r':{k:rsub(f'r/{k}/','API16E') for k in ('scale16','control','scale20')},
         'labels_c':{k:rsub(f'c/{k}/','API16E_c1') for k in ('scale16','control','scale20')},
         'part_r':_psum(rpc,'r'),'part_c':_psum(rpc,'c'),'replay_compare':rpc,
         'misfires_main':{arm:sum(1 for v in main_ if arm in v and v[arm]['misfire']) for arm in ('API16E','API16E_b')},
         'replay_wrong':{p:sum(v[a]['label']=='WRONG' for k,v in rp.items() if k.startswith(p+'/') for a in v) for p in ('r','c')},
         'amb_rule_applied':sum('amb_rule' in v[a] for v in allv for a in v),
         'words_unsound':sum(v[a]['words_unsound'] for v in allv for a in v),
         'words_checked':sum(v[a]['words_checked'] for v in allv for a in v),
         'truth_inconsistent':sum(sum(v[a]['truth_inconsistent_rounds'] for a in v)+sum(not x['truth_consistent_final'] for x in v.values()) for v in allv),
         'mismatching_cases':len(bad),'mismatches':{k:v for k,v in list(bad.items())[:50]},'per_case':per,'per_replay':rp,
         'PASS':not bad and len(per)>0}
    write_new(d/'RECOUNT_049.json',out);print(json.dumps({k:v for k,v in out.items() if k not in ('per_case','per_replay','replay_compare')},default=str));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
