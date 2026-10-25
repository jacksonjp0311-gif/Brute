"""Bridge acceptance tests (bridge/BRIDGE_PLAN.md: v0.1 criteria B1-B9 on brute.api/1.1, v0.2 addendum B10-B14 on 1.2)."""
import ast,json,subprocess,sys,time,unittest
from pathlib import Path
from tests.bridge_corpus import sessions,rows,ROOT,drive
from bridge.audit import audit
from bridge.replay import replay
from bridge.session import Bridge
from bridge.claims import check_claim,READING
STDLIB=set(sys.stdlib_module_names)


def imports(p):
    for n in ast.walk(ast.parse(p.read_text())):
        if isinstance(n,ast.Import):
            for a in n.names:yield a.name,0
        elif isinstance(n,ast.ImportFrom):yield n.module or '',n.level


class Grounding(unittest.TestCase):  # B1, B4, B5, B6
    def test_audit_all_sessions(self):
        total={'claims':0,'requests':0,'unsupported':0,'request_action':0}
        for name,b in sessions().items():
            v,n=audit(rows(b));self.assertEqual(v,[],name)
            for k in total:total[k]+=n[k]
        self.assertGreater(total['claims'],5000);self.assertGreater(total['requests'],0)
        self.assertEqual(total['request_action'],0)  # B6: no experiment field in brute.api/1.1
        print('\n[bridge corpus]',json.dumps(total),file=sys.stderr)

    def test_statuses_and_requests_covered(self):
        st=set();kinds=set()
        for b in sessions().values():
            for r in rows(b):
                for d in r.get('trace_docs',{}).values():st.add(d['response']['status']+'/'+str(d['response']['reason']))
                kinds|={q['kind']+':'+q['claims'][0]['template'] for q in r.get('requests',[])}
        for need in ('CERTIFIED/None','POSSIBLE_SET/None','ABSTAIN/MARGIN_DISAGREES','OUT_OF_FAMILY/FAMILY_CONTRADICTED',
                     'OUT_OF_FAMILY/RESIDUAL_SURPRISE','ERROR/NOT_INITIALIZED'):self.assertIn(need,st)
        for need in ('CONTRADICTION_NOTICE:req.contradiction','SCOPE_ALERT:req.scope.residual','SCOPE_ALERT:req.scope.attestation',
                     'REQUEST_OBSERVATION:req.observation'):self.assertIn(need,kinds)

    def test_retraction_claims_present(self):
        b=sessions()['edge_attested_contradiction'];a=[r for r in rows(b) if r['type']=='turn' and r['answer']['intent']=='retractions'][-1]['answer']
        self.assertTrue(any(c['template']=='retraction' and c['label']=='Rejected' for c in a['claims']))

    def test_tampering_detected(self):
        r=[x for x in rows(sessions()['cycle3']) if x['type']=='turn' and x['answer']['claims']]
        traces={};[traces.update(x['trace_docs']) for x in rows(sessions()['cycle3']) if x['type']=='turn']
        c=dict(r[3]['answer']['claims'][0]);self.assertEqual(check_claim(c,traces),[])
        self.assertTrue(check_claim(dict(c,text=c['text']+' Probably.'),traces))
        self.assertTrue(check_claim(dict(c,template='free'),traces))
        self.assertTrue(check_claim(dict(c,label='Exact' if c['label']!='Exact' else 'Inferred'),traces))
        self.assertTrue(check_claim(dict(c,field_refs=['nope#/response/status','nope#/response/op']),traces))
        rows_=rows(sessions()['cycle3']);rows_[5]=json.loads(json.dumps(rows_[5]))
        rows_[5]['requests']=rows_[5]['requests']+[{'request_id':'q999','kind':'REQUEST_ACTION','trace_id':'x','claims':[]}]
        self.assertTrue(audit(rows_)[0])


class Unsupported(unittest.TestCase):  # B2
    def test_zero_claims_zero_calls(self):
        b=Bridge(api='1.1');b.ask('init',obs={'x':0,'y':1})
        for line,intent in (('split','split'),('which action best splits?','split'),('which models disagree','models'),
                            ('tell me a joke','unknown'),('are you conscious','unknown'),('predict c','unknown'),('init x=3 y=0','unknown')):
            from bridge.parse import parse
            i,args=parse(line);self.assertEqual(i,intent,line)
            n=b.calls;a,q=b.ask(i,command=line,**args)
            self.assertEqual((a['status'],a['claims'],b.calls,q),('UNSUPPORTED',[],n,[]),line)
        self.assertEqual(sum(json.loads(l)['kind']=='unsupported_intent' for l in b.flags.lines),7)

    def test_split_hook_renders_only_with_field(self):
        class Fake:  # a 1.1 service that happens to return an `experiment` field (the v0.1 forward hook)
            def __init__(s):
                from brute.api.service_v011 import BruteServiceV011;s.s=BruteServiceV011()
            def handle(s,req):
                r=s.s.handle(req)
                if req['op']=='predict':r=dict(r,experiment={'action':'b','score':3,'rule':'fake rule','tie_break':'default_action','tied':False})
                return r
        b=Bridge(service=Fake(),api='1.1');b.ask('init',obs={'x':0,'y':1});a,q=b.ask('predict',action='a')
        self.assertEqual([x['kind'] for x in q],['REQUEST_ACTION'])
        a,_=b.ask('split');self.assertEqual(a['status'],'ANSWERED');self.assertEqual(a['claims'][0]['template'],'experiment')
        self.assertEqual(audit(rows(b))[0],[])


class Boundary(unittest.TestCase):  # B3, B9
    def test_bridge_imports(self):
        files=list((ROOT/'bridge').rglob('*.py'));self.assertTrue(files)
        for p in files:
            for mod,level in imports(p):
                if level:continue
                top=mod.split('.')[0]
                ok=top in STDLIB or mod=='brute.api' or mod.startswith('brute.api.') or mod.startswith('adapters.language') or top=='bridge'
                self.assertTrue(ok,f'{p.name} imports {mod}')
                for banned in ('brute.core','brute.active','brute.fallback','brute.evaluation','bgr','experiments','scripts','numpy'):self.assertFalse(mod.startswith(banned),f'{p.name}: {mod}')

    def test_audit_modules_stdlib_only(self):
        for name in ('claims','templates','triggers','audit','log','parse'):
            for mod,level in imports(ROOT/'bridge'/f'{name}.py'):
                self.assertTrue(level or mod.split('.')[0] in STDLIB,f'{name} imports {mod}')

    def test_file_io_only_in_log(self):
        for p in (ROOT/'bridge').rglob('*.py'):
            if p.name=='log.py':continue
            for n in ast.walk(ast.parse(p.read_text())):
                if isinstance(n,ast.Name):self.assertNotIn(n.id,('open','eval','exec','__import__'),p.name)
                if isinstance(n,ast.Attribute):self.assertNotIn(n.attr,('read_text','write_text','read_bytes','environ'),p.name)

    def test_core_never_imports_bridge(self):
        for d in ('brute','bgr89','bgr90','experiments','scripts','adapters'):
            for p in (ROOT/d).rglob('*.py') if (ROOT/d).exists() else []:
                for mod,level in imports(p):self.assertFalse(level==0 and mod.split('.')[0]=='bridge',f'{p}: {mod}')

    def test_core_untouched(self):
        out=subprocess.run(['git','diff','--stat','origin/main','--','brute','bgr89','bgr90','experiments','results'],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(out.returncode,0);self.assertEqual(out.stdout.strip(),'')


class Determinism(unittest.TestCase):  # B7, B8
    def test_replay_byte_identical(self):
        for name,b in sessions().items():
            if name=='edge_residual':continue  # non-default tau; replay uses the default service
            n,bad=replay(rows(b));self.assertGreater(n,0);self.assertEqual(bad,[],name)

    def test_transcripts_reproduce(self):
        from tests.bridge_corpus import cases,commands
        c=cases()['ood5'];a=drive(Bridge(source='x',api='1.1'),commands(c));b=drive(Bridge(source='x',api='1.1'),commands(c))
        self.assertEqual(a.transcript.lines,b.transcript.lines)

    def test_query_speed(self):  # B8 restated: median wall time per ask over the study-004 cycle3 session
        from tests.bridge_corpus_004 import cases,drive
        import bridge.session as S
        ts=[];ex=[];orig=S.Bridge.ask
        def timed(self,*a,**k):
            t=time.perf_counter();r=orig(self,*a,**k);(ex if a[0] in ('split','models') else ts).append(time.perf_counter()-t);return r
        S.Bridge.ask=timed
        try:drive(cases()['cycle3'])
        finally:S.Bridge.ask=orig
        ts.sort();med=ts[len(ts)//2];ex.sort()
        print(f'\n[bridge speed] median {med*1000:.2f} ms over {len(ts)} asks; experiment asks (core cost, reported only) median {ex[len(ex)//2]*1000:.1f} ms, max {ex[-1]*1000:.1f} ms over {len(ex)}',file=sys.stderr)
        self.assertLess(med,0.05)


class Api12(unittest.TestCase):  # v0.2 addendum B10-B12
    @classmethod
    def setUpClass(cls):
        from tests.bridge_corpus_004 import sessions,cases
        cls.S=sessions();cls.C=cases()

    def test_b11_matches_study_004(self):
        self.assertEqual(len(self.S),7)
        for fam,(b,bad) in self.S.items():self.assertEqual(bad,[],fam)

    def test_b12_audit_and_requests(self):
        tot={}
        for fam,(b,_) in self.S.items():
            v,n=audit(rows(b));self.assertEqual(v,[],fam)
            for k,x in n.items():tot[k]=tot.get(k,0)+x
        self.assertEqual(tot['request_action'],tot['untied']);self.assertGreater(tot['request_action'],0)
        self.assertEqual(tot['experiments'],7*44*2)
        print('\n[bridge corpus 1.2]',json.dumps(tot,sort_keys=True),file=sys.stderr)

    def test_b10_experiment_is_read_only(self):
        from tests.bridge_corpus_004 import drive
        def plain(b):
            out=[]
            for t,d in b.traces.items():
                if d['request']['op']=='experiment':continue
                out.append(json.dumps({k:v for k,v in d['response'].items() if k!='request_id'},sort_keys=True))
            return out
        for fam,c in self.C.items():
            without,_=drive(c,experiments=False);self.assertEqual(plain(self.S[fam][0]),plain(without),fam)

    def test_templates_and_flags_covered(self):
        tpl=set();kinds=set();flags=set()
        for b,_ in self.S.values():
            for r in rows(b):
                if r['type']!='turn':continue
                tpl|={c['template'] for c in r['answer']['claims']};kinds|={q['kind'] for q in r['requests']}
            flags|={json.loads(l)['kind'] for l in b.flags.lines}
        for t in ('experiment','experiment.score','experiment.tied','counts.rows','counts.code','counts.margin'):self.assertIn(t,tpl)
        self.assertIn('REQUEST_ACTION',kinds)

    def test_replay_byte_identical_12(self):
        b,_=self.S['cycle3'];n,bad=replay(rows(b));self.assertGreater(n,0);self.assertEqual(bad,[])

    def test_override_flag(self):
        b=Bridge();b.ask('init',obs={'x':0,'y':0})
        for i in range(6):b.ask('observe',action='a',obs={'x':i%2,'y':0})
        a,q=b.ask('split',default_action='a')
        e=b.traces[b.last]['response']['experiment']
        if e['tied']:self.skipTest('tied here')
        other='ba'['ab'.index(e['action'])]
        b.ask('observe',action=other,obs={'x':0,'y':0})
        self.assertIn('request_action_overridden',[json.loads(l)['kind'] for l in b.flags.lines])
        self.assertEqual(audit(rows(b))[0],[])

    def test_models_unsupported_without_counts_under_11(self):
        b=Bridge(api='1.1');b.ask('init',obs={'x':0,'y':0});n=b.calls
        a,_=b.ask('models');self.assertEqual((a['status'],b.calls),('UNSUPPORTED',n))


class Cli(unittest.TestCase):
    def test_script_and_audit(self):
        import tempfile,os
        d=tempfile.mkdtemp();s=os.path.join(d,'s.cmds')
        with open(s,'w') as fh:fh.write('init x=0 y=1\npredict a\nwhy\nsplit\nquit\n')
        t=os.path.join(d,'t.jsonl');f=os.path.join(d,'f.jsonl')
        r=subprocess.run([sys.executable,'-m','bridge','--api','1.1','--script',s,'--transcript',t,'--flags',f],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr);self.assertIn('[UNSUPPORTED] split',r.stdout)
        r=subprocess.run([sys.executable,'-m','bridge.audit',t],cwd=ROOT,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stdout)
        r=subprocess.run([sys.executable,'-m','bridge','--script',s,'--transcript',t+'2','--flags',f],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr);self.assertIn('[ANSWERED] split',r.stdout);t=t+'2'
        r=subprocess.run([sys.executable,'-m','bridge.audit',t],cwd=ROOT,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stdout)


if __name__=='__main__':unittest.main()
