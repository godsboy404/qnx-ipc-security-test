"""Deterministic review baseline. The LLM review stage remains a human-controlled integration task."""
def review(item):
    if item.get('approved_na') is True:
        status, reason = 'NOT_APPLICABLE', 'preapproved scope'
    elif not item.get('evidence_exists') or not item.get('same_version'):
        status, reason = 'INSUFFICIENT_EVIDENCE', 'missing or mismatched evidence'
    elif item.get('observed') == 'counterexample':
        status, reason = 'FAIL', 'observable counterexample'
    elif item.get('observed') == 'supports':
        status, reason = 'PASS', 'evidence supports this limited criterion'
    else:
        status, reason = 'INSUFFICIENT_EVIDENCE', 'claim only or unknown observation'
    return {'criterion_id':item['criterion_id'], 'status':status, 'reason':reason,
            'scope':'calibration fixture only', 'evidence_level':'fixture_demo',
            'score_suggestion':None,'human_signoff':'pending','llm_review':'not_implemented'}
