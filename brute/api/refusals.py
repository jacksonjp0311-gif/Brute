"""Canonical refusal sentences. Adapters must reproduce them byte-for-byte."""
REFUSALS={
 'MARGIN_DISAGREES':'A model with one more hidden state could produce a different reading; Brute will not certify a single value.',
 'BOUND_SATURATED':'Every surviving explanation uses all available hidden states, so the state bound may be too small; Brute will not certify.',
 'RESIDUAL_SURPRISE':'Recent readings are more surprising than anything seen in calibration; Brute treats the world as outside its family and will not certify.',
 'BUDGET_EXHAUSTED':'The hypothesis budget ran out; the evidence is kept, and Brute will not predict until it is replayed with a larger budget.',
 'UNATTESTED_SCOPE':'No valid scope attestation names this family, so Brute will not issue a public certificate.',
 'FAMILY_CONTRADICTED':'No machine in the declared family is consistent with the evidence; Brute will not predict.',
 'NOT_INITIALIZED':'This session has no initial observation yet.',
 'INVALID_REQUEST':'The request does not match the brute.api/1.0 schema.',
 'INTERNAL':'Brute hit an internal error and returned no claim.',
}


def refusal_text(reason):
    if reason is None:return None
    return REFUSALS[reason.value if hasattr(reason,'value') else reason]
