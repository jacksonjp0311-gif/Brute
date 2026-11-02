import sys,time,itertools,json
sys.argv=[sys.argv[0],'0','0']+sys.argv[1:]
exec(open('/tmp/s58/proto.py').read().split('seed=int')[0])
D57=json.load(open('results/study-057/main/RESULTS.json'))
arm=sys.argv[3]
for c in D57['cases'][:int(sys.argv[4])]:
    seed=c['seed'];a=c['arms'][arm];w=W50.world(seed,'scale20');masks,acts,rd=passive(StepWorld(w),seed)
    acts=acts+list(a['extra_acts']);masks=masks+list(a['extra_masks'])
    R=Inc14(20,3,4,'g3').sync(masks,acts);r,sp=solve(R,[],400000)
    mod=set(x for x in R.s.get_model() if x>0);d,e=R.machine(mod);ok,s,_=simulate(d,e,acts,masks)
    q=w.start
    for x in acts:q=w.transitions[q][x]
    out=[]
    for word in [[0],[1],[2],[0,0],[1,1],[2,2]]:
        p=run_word(d,e,s,word);v=R._v;g=v();cl=[];n=20;h=len(word)
        y=[[v() for _ in range(n)] for _ in range(h+1)];Dd=[v() for _ in range(h+1)]
        for q_ in range(n):cl+= [[-R.x[R.T][q_],y[0][q_]],[R.x[R.T][q_],-y[0][q_]]]
        for j in range(1,h+1):
            cl.append(y[j])
            for i in range(n):
                for i2 in range(i+1,n):cl.append([-y[j][i],-y[j][i2]])
            for q_ in range(n):
                for r_ in range(n):cl.append([-y[j-1][q_],-R.d[q_][word[j-1]][r_],y[j][r_]])
            for q_ in range(n):cl.append([-Dd[j],-y[j][q_],-R.e[q_][p[j-1]]])
        cl.append(Dd[1:])
        for cc in cl:R.s.add_clause([-g]+cc)
        t=time.time();res,sp=solve(R,[g],200000);R.s.add_clause([-g])
        out.append((''.join(map(str,word)),{True:'S',False:'U',None:'?'}[res],sp,round(time.time()-t,1),p==run_word(w.transitions,w.emissions,q,word)))
    print(seed,a['label'],len(acts),out,flush=True)
