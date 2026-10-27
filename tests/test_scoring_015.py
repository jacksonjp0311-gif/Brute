"""Study-015 scoring scripts (make_paired_015, make_reproducibility_015, make_gates_015, clean_clone_015) on a 2-case
smoke-transfer study built in a temp directory (smoke seeds only; no held-out seed). Checks the own-trajectory recount,
injected errors are caught by G_recount / GS_a3 / GS_b3, missing inputs fail with a reason, heartbeat gaps are attributed."""
import json,shutil,tempfile,unittest
from pathlib import Path
from experiments import brute_study_015 as BS
from experiments.brute_common_015 import sha,load,PLAN
from scripts import make_paired_015 as MP,make_gates_015 as MG,make_reproducibility_015 as MR,clean_clone_015 as CC

_D=None
def study():
    global _D
    if _D is None:
        _D=Path(tempfile.mkdtemp(prefix='brute-score-015-'));BS.run(_D/'transfer',1,'smoke-transfer',limit=2)
    return _D


def copy_with(mut):
    d=Path(tempfile.mkdtemp(prefix='brute-score-015m-'));shutil.copytree(study()/'transfer',d/'transfer')
    p=d/'transfer'/'SCIENTIFIC.json';o=json.loads(p.read_text());mut(o['cases']);p.write_text(json.dumps(o,sort_keys=True))
    s=json.loads((d/'transfer'/'SEAL.json').read_text());s['scientific_sha256']=sha(p);(d/'transfer'/'SEAL.json').write_text(json.dumps(s))
    return d


def obs(g):return g.get('observed') or g.get('observed_on_available_inputs')


class Paired015(unittest.TestCase):
    def test_contrasts(self):
        o=MP.build(study(),smoke=True);cs=[c for c in load(study()/'transfer'/'SCIENTIFIC.json')['cases'] if c['family']!='ood5']
        for a in MP.MAIN_ARMS:self.assertAlmostEqual(o['S_'+a]['mean'],sum(c['summary']['S'][a] for c in cs)/len(cs),5)
        m=sum(c['summary']['S']['RSX4']-c['summary']['S']['RG4'] for c in cs)/len(cs);self.assertAlmostEqual(o['TV_RSX4']['mean'],m,5)
        self.assertEqual(o['resamples'],2000);self.assertEqual(o['seed'],20261027)
        self.assertEqual(MP.build(study(),smoke=True),o)

    def test_contrast_cluster(self):
        cs=[{'family':'cycle3','seed':s,'x':v} for s,v in ((1,1),(1,1),(2,3))]
        r=MP.contrast(cs,lambda c:c['x'],'x');self.assertAlmostEqual(r['mean'],5/3,5);self.assertEqual(r['families']['cycle3']['seeds'],2)


class Gates015(unittest.TestCase):
    def test_clean_smoke(self):
        g=MG.build(study(),smoke=True)['gates']
        rc=obs(g['G_recount'])
        self.assertEqual(rc['mismatches'],[]);self.assertIn('RSX4',rc['per_block_arm']['transfer'])
        for k in ('GRS_region_split','GS_c3_wrong_family','GTI_test_isolation','GAPI3_certify3'):self.assertIn('INCOMPLETE_INPUT',g[k]['reason'])
        self.assertEqual(obs(g['GS_b3_containment'])['cases_failing'],0)

    def test_rsx_recount_uses_rsx_trajectory(self):
        def mut(cs):
            c=cs[0];A=MG.actuals(c)['RSX'];tr=c['transfer']['RSX4']['trace']
            i=next(i for i,r in enumerate(tr) if r['certificate'][0] is not None);tr[i]['certificate'][0]=(A[i][0]+1)%4
        g=MG.build(copy_with(mut),smoke=True)['gates']
        self.assertTrue(any(m[1]=='RSX4' for m in obs(g['G_recount'])['mismatches']))
        self.assertFalse(obs(g['GS_a3_soundness'])['per_arm']['RSX4']['pass'])
        self.assertGreater(obs(g['GS_b3_containment'])['cases_failing'],0)

    def test_recorded_count_tamper(self):
        def mut(cs):cs[1]['transfer']['DLFp']['false_certificates']+=1
        g=MG.build(copy_with(mut),smoke=True)['gates'];self.assertFalse(g['G_recount']['pass'])

    def test_heartbeat_attribution(self):
        d=Path(tempfile.mkdtemp());rows=[{'wall':100.0+t,'monotonic':t,'boottime':t,'cpu_s':0,'psi_io_some_us':0,'psi_io_full_us':0} for t in (0,1,13,14)]
        (d/'HEARTBEAT_015.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
        h=MG.heartbeat(d,100.5);self.assertEqual(h['beats'],3);self.assertEqual(len(h['gaps_over_10s']),1);self.assertEqual(h['max_gap_s'],12.0)

    def test_registration(self):
        C=load(PLAN)['criteria'];o=MG.build(study(),smoke=True)
        self.assertEqual(sorted(C),sorted(o['criteria_scored']))


class Repro015(unittest.TestCase):
    def test_strip_and_diff(self):
        a={'x':1,'wall_informational':3,'y':{'case_wall_informational':2,'z':[1,2]}};b={'x':1,'y':{'z':[1,3]}}
        self.assertEqual(MR.strip_timing(a),{'x':1,'y':{'z':[1,2]}});self.assertIsNotNone(MR.first_diff(MR.strip_timing(a),b))


class CleanClone015(unittest.TestCase):
    def test_inputs(self):
        self.assertIn('results/study-015/transfer/SCIENTIFIC.json',CC.RAW_GZ);self.assertIn('results/study-015/GATES_015.json',CC.TRACKED)
        self.assertTrue(all('014' not in f for f in CC.TRACKED+CC.RAW_GZ))


if __name__=='__main__':unittest.main()
