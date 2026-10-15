def ratio(a,b):
    return a/b if b else None

def summarize(rows):
    normal = [r for r in rows if r['oracle_label'] == 'valid']
    invalid = [r for r in rows if r['oracle_label'] == 'invalid']
    prevented = [r for r in invalid if r['decision'] in ('BLOCK','RATE_LIMIT')]
    bypass = [r for r in invalid if r['decision'] == 'ALLOW']
    return {'total':len(rows), 'valid_total':len(normal), 'invalid_total':len(invalid),
        'false_positive_rate':ratio(sum(r['decision'] != 'ALLOW' for r in normal),len(normal)),
        'invalid_prevention_rate':ratio(len(prevented),len(invalid)),
        'invalid_allow_rate':ratio(len(bypass),len(invalid)),
        'simulated_fault_count':sum(r['target_outcome']=='SIMULATED_FAULT' for r in rows),
        'qnx_crash_count':None,'isolation_success_rate':None,
        'limitations':['simulation only','no real process probes','no QNX performance or isolation claim'],
        'metric_unit':'one logical test case', 'undefined_ratio':'null when denominator is zero'}
