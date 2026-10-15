def isolation_verdict(probes):
    """Require complete external observations; a timeout alone proves no crash."""
    required = ('target_fault_confirmed','client_ok','peer_ok','service_ok','system_ok','recovered')
    if any(probes.get(k) is None for k in required):
        return 'INCONCLUSIVE'
    if not probes['target_fault_confirmed']:
        return 'NOT_APPLICABLE'
    return 'PASS' if all(probes[k] for k in required[1:]) else 'FAIL'

def unknown_probes():
    return dict.fromkeys(('target_fault_confirmed','client_ok','peer_ok','service_ok','system_ok','recovered'))
