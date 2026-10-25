"""Bridge v0.1 acceptance tests (bridge/BRIDGE_PLAN.md, criteria B1-B9)."""
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
        b=Bridge();b.ask('init',obs={'x':0,'y':1})
        for line,intent in (('split','split'),('which action best splits?','split'),('which models disagree','models'),
                            ('tell me a joke','unknown'),('are you conscious','unknown'),('predict c','unknown'),('init x=3 y=0','unknown')):
            from bridge.parse import parse
            i,args=parse(line);self.assertEqual(i,intent,line)
            n=b.calls;a,q=b.ask(i,command=line,**args)
            self.assertEqual((a['status'],a['claims'],b.calls,q),('UNSUPPORTED',[],n,[]),line)
        self.assertEqual(sum(json.loads(l)['kind']=='unsupported_intent' for l in b.flags.lines),7)

    def test_split_hook_renders_only_with_field(self):
        class Fake:  # stands in for a future v0.2.0 service that returns an `experiment` field
            def __init__(s):
                from brute.api.service_v011 import BruteServiceV011;s.s=BruteServiceV011()
            def handle(s,req):
                r=s.s.handle(req)
                if req['op']=='predict':r=dict(r,experiment={'action':'b','score':3})
                return r
        b=Bridge(service=Fake());b.ask('init',obs={'x':0,'y':1});a,q=b.ask('predict',action='a')
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
                for banned in ('brute.core','brute.fallback','brute.evaluation','bgr','experiments','scripts','numpy'):self.assertFalse(mod.startswith(banned),f'{p.name}: {mod}')

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
        out=subprocess.run(['git','diff','--stat','main','--','brute','bgr89','bgr90','experiments','results'],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(out.returncode,0);self.assertEqual(out.stdout.strip(),'')


class Determinism(unittest.TestCase):  # B7, B8
    def test_replay_byte_identical(self):
        for name,b in sessions().items():
            if name=='edge_residual':continue  # non-default tau; replay uses the default service
            n,bad=replay(rows(b));self.assertGreater(n,0);self.assertEqual(bad,[],name)

    def test_transcripts_reproduce(self):
        from tests.bridge_corpus import cases,commands
        c=cases()['ood5'];a=drive(Bridge(source='x'),commands(c));b=drive(Bridge(source='x'),commands(c))
        self.assertEqual(a.transcript.lines,b.transcript.lines)

    def test_query_speed(self):
        from tests.bridge_corpus import cases,commands
        c=cases()['cycle3'];b=Bridge();ts=[]
        from bridge.parse import parse
        for l in commands(c):
            i,args=parse(l);t=time.perf_counter();b.ask(i,command=l,**args);ts.append(time.perf_counter()-t)
        ts.sort();med=ts[len(ts)//2];print(f'\n[bridge speed] median {med*1000:.2f} ms over {len(ts)} queries',file=sys.stderr)
        self.assertLess(med,0.05)


class Cli(unittest.TestCase):
    def test_script_and_audit(self):
        import tempfile,os
        d=tempfile.mkdtemp();s=os.path.join(d,'s.cmds')
        with open(s,'w') as fh:fh.write('init x=0 y=1\npredict a\nwhy\nsplit\nquit\n')
        t=os.path.join(d,'t.jsonl');f=os.path.join(d,'f.jsonl')
        r=subprocess.run([sys.executable,'-m','bridge','--script',s,'--transcript',t,'--flags',f],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr);self.assertIn('[UNSUPPORTED] split',r.stdout)
        r=subprocess.run([sys.executable,'-m','bridge.audit',t],cwd=ROOT,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stdout)


if __name__=='__main__':unittest.main()
