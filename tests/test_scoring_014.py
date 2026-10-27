"""Study-014 scoring scripts (make_paired_014, make_reproducibility_014, make_gates_014, clean_clone_014) on a 2-case
smoke-transfer study built in a temp directory (smoke seeds only; no held-out seed). Checks the recomputed false
counts, injected errors are caught, missing inputs fail with a reason, heartbeat gaps are attributed."""
import json,shutil,tempfile,unittest
from pathlib import Path
from experiments import brute_study_014 as BS
from experiments.brute_common_014 import sha,load,PLAN
from scripts import make_paired_014 as MP,make_gates_014 as MG,make_reproducibility_014 as MR,clean_clone_014 as CC

_D=None
def study():
    global _D
    if _D is None:
        _D=Path(tempfile.mkdtemp(prefix='brute-score-014-'));BS.run(_D/'transfer',1,'smoke-transfer',limit=2)
    return _D


def copy_with(mut):
    d=Path(tempfile.mkdtemp(prefix='brute-score-014m-'));shutil.copytree(study()/'transfer',d/'transfer')
    p=d/'transfer'/'SCIENTIFIC.json';o=json.loads(p.read_text());mut(o['cases']);p.write_text(json.dumps(o,sort_keys=True))
    s=json.loads((d/'transfer'/'SEAL.json').read_text());s['scientific_sha256']=sha(p);(d/'transfer'/'SEAL.json').write_text(json.dumps(s))
    return d


class Paired014(unittest.TestCase):
    def test_contrasts(self):
        o=MP.build(study(),smoke=True);cs=load(study()/'transfer'/'SCIENTIFIC.json')['cases']
        for a in BS.ARMS:self.assertAlmostEqual(o['S_'+a]['mean'],sum(c['summary']['S'][a] for c in cs)/len(cs),5)
        m=sum(c['summary']['S']['DLFp']-c['summary']['S']['RG4'] for c in cs)/len(cs);self.assertAlmostEqual(o['TV_DLFp']['mean'],m,5)
        self.assertEqual(o['resamples'],2000);self.assertEqual(o['seed'],20261026)
        self.assertEqual(MP.build(study(),smoke=True),o)

    def test_contrast_cluster(self):
        cs=[{'family':'cycle3','seed':s,'x':v} for s,v in ((1,1),(1,1),(2,3))]
        r=MP.contrast(cs,lambda c:c['x'],'x');self.assertAlmostEqual(r['mean'],5/3,5);self.assertEqual(r['families']['cycle3']['seeds'],2)


class Gates014(unittest.TestCase):
    def test_clean_smoke(self):
        o=MG.build(study(),smoke=True);g=o['gates']
        self.assertTrue(g['GS_a_soundness']['observed_on_available_inputs']['per_arm']['DLFp']['pass'] if 'reason' in g['GS_a_soundness'] else g['GS_a_soundness']['observed']['per_arm']['DLFp']['pass'])
        for k in ('GS_d_transfer_value','GS_x_discriminating_experiments','GTI_test_isolation'):self.assertIn('INCOMPLETE_INPUT',g[k]['reason'])
        self.assertFalse(g['GS_d_transfer_value']['pass'])

    def _obs(self,g):return g.get('observed') or g.get('observed_on_available_inputs')

    def test_injected_false_certificate(self):
        def mut(cs):
            c=cs[0];A=MG.actuals(c)['SP8'];tr=c['transfer']['DLFp']['trace']
            i=next(i for i,r in enumerate(tr) if r['certificate'][0] is not None);tr[i]['certificate'][0]=1-A[i][0]
        o=MG.build(copy_with(mut),smoke=True);pa=self._obs(o['gates']['GS_a_soundness'])['per_arm']['DLFp']
        self.assertEqual(pa['recomputed_false'],1);self.assertFalse(pa['pass'])
        self.assertGreater(self._obs(o['gates']['GS_b_containment'])['cases_failing'],0)

    def test_containment_order(self):
        def mut(cs):cs[1]['summary']['S']['RG4']=cs[1]['summary']['S']['DLFn']+1
        o=MG.build(copy_with(mut),smoke=True);self.assertEqual(self._obs(o['gates']['GS_b_containment'])['cases_failing'],1)

    def test_heartbeat_attribution(self):
        d=Path(tempfile.mkdtemp());rows=[{'wall':100.0+t,'monotonic':t,'boottime':t,'cpu_s':0,'psi_io_some_us':0,'psi_io_full_us':0} for t in (0,1,13,14)]
        (d/'HEARTBEAT_014.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
        h=MG.heartbeat(d,100.5);self.assertEqual(h['beats'],3);self.assertEqual(len(h['gaps_over_10s']),1);self.assertEqual(h['max_gap_s'],12.0)

    def test_registration(self):
        C=load(PLAN)['criteria']
        for k in ('GS_a','GS_b','GS_c','GS_d','GS_rg','GS_x','G_alias','GS_ref','GAPI2','G10','G12','G13','GTI','G_RT','G_HB'):
            self.assertTrue(any(x.startswith(k) for x in C),k)


class Repro014(unittest.TestCase):
    def test_strip_and_diff(self):
        a={'x':1,'wall_informational':3,'y':{'case_wall_informational':2,'z':[1,2]}};b={'x':1,'y':{'z':[1,3]}}
        self.assertEqual(MR.strip_timing(a),{'x':1,'y':{'z':[1,2]}});self.assertIsNotNone(MR.first_diff(MR.strip_timing(a),b))
        self.assertEqual(MR._canon(a),MR._canon({'x':1,'y':{'z':[1,2]}}))


class CleanClone014(unittest.TestCase):
    def test_inputs(self):
        self.assertIn('results/study-014/transfer/SCIENTIFIC.json',CC.RAW_GZ);self.assertIn('results/study-014/GATES_014.json',CC.TRACKED)
        self.assertTrue(all('013' not in f for f in CC.TRACKED+CC.RAW_GZ))


if __name__=='__main__':unittest.main()
