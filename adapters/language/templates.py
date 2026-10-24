"""Fixed sentence templates. Every slot is filled from a JSON pointer into the response.

A template applies only when its `when` predicate holds on the response; the checker
enforces the same predicate, so a public-scope sentence cannot be attached to a
conditional certificate and no value can be named outside CERTIFIED.
"""
from __future__ import annotations


def fmt_reading(v):
    return ', '.join(f'{k}={v[k]}' for k in sorted(v))


def fmt_set(vs):
    return '; '.join('{'+fmt_reading(v)+'}' for v in vs)


def fmt_plain(v):
    return str(v)


FORMATTERS={'reading':fmt_reading,'set':fmt_set,'plain':fmt_plain}


def _st(*statuses):return lambda r:r['status'] in statuses
def _cert(kind):return lambda r:r['status']=='CERTIFIED' and r['certificate'] is not None and r['certificate']['kind']==kind

# id -> (format string, [(pointer, formatter)], when, role)
TEMPLATES={
 'certified.conditional':('If the world is in the family {0}, the next reading is {1}.',
     [('/certificate/conditional_on','plain'),('/certificate/value','reading')],_cert('conditional'),'prediction'),
 'certified.public':('Within the attested scope {0} (attestation {1}), the next reading is {2}.',
     [('/certificate/conditional_on','plain'),('/evidence/attestation_id','plain'),('/certificate/value','reading')],_cert('public'),'prediction'),
 'certified.basis':('This rests on {0} surviving explanations after {1} observations; a {2}-state check agrees.',
     [('/evidence/surviving_rows','plain'),('/evidence/evidence_count','plain'),('/evidence/margin/states','plain')],_st('CERTIFIED'),'evidence'),
 'possible_set.values':('The next reading is one of: {0}.',[('/support','set')],_st('POSSIBLE_SET'),'evidence'),
 'possible_set.status':('Brute reports status {0}: it cannot narrow the next reading to one value.',[('/status','plain')],_st('POSSIBLE_SET'),'evidence'),
 'refusal':('{0}',[('/refusal_text','plain')],lambda r:r['refusal_text'] is not None,'refusal'),
 'margin.detail':('A {0}-state check leaves {1} possible readings.',
     [('/evidence/margin/states','plain'),('/evidence/margin/support_size','plain')],
     lambda r:r['reason']=='MARGIN_DISAGREES','evidence'),
 'residual.detail':('Windowed surprise {0} is above the calibrated threshold {1}.',
     [('/evidence/residual/surprise','plain'),('/evidence/residual/threshold','plain')],
     lambda r:r['reason']=='RESIDUAL_SURPRISE','evidence'),
 'retraction':('The certificate issued for step {0} is withdrawn.',[('/retractions/{i}/step','plain')],
     lambda r:bool(r['retractions']),'retraction'),
 'acknowledged':('Recorded; {0} observations so far.',[('/evidence/evidence_count','plain')],_st('ACKNOWLEDGED'),'evidence'),
}

# Which templates render for each response, in order.
ORDER=('certified.conditional','certified.public','certified.basis','possible_set.status','possible_set.values',
       'refusal','margin.detail','residual.detail','retraction','acknowledged')
