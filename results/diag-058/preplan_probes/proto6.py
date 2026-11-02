import sys,time,json
idx=int(sys.argv[1]);T=int(sys.argv[2])
sys.argv=[sys.argv[0],'0','0']
exec(open('/tmp/s58/proto.py').read().split('seed=int')[0])
D57=json.load(open('results/study-057/main/RESULTS.json'))
c=D57['cases'][idx];seed=c['seed'];a=c['arms']['COV_O'];w=W50.world(seed,'scale20');masks,acts,rd=passive(StepWorld(w),seed)
acts=(acts+list(a['extra_acts']))[:T];masks=(masks+list(a['extra_masks']))[:T+1]
R=Inc14(20,3,4,'g3').sync(masks,acts);t=time.time();r,sp=solve(R,[],10**9);print(seed,T,r,sp,round(time.time()-t,1),flush=True)
