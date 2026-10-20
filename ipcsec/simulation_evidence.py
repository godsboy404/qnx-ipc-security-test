"""OBS-01: read-only consistency/reanalysis of explicitly selected simulation runs."""
import hashlib
import json
from pathlib import Path
from .model import Case
from .defense import Defense
from .harness import SimulationTarget
from .runner import oracle
from .metrics import summarize


def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def rows(path):return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines()]


def verify(folder):
    folder=Path(folder).resolve()
    manifest=read(folder/'manifest.json')
    if manifest['run_id']!=folder.name or manifest['backend']!='simulation':raise ValueError('Simulation identity mismatch')
    hashes=manifest['evidence_hashes']
    if set(hashes)!={'cases.jsonl','results.jsonl','summary.json'}:raise ValueError('Missing simulation dependencies')
    for name,value in hashes.items():
        path=folder/name
        if path.is_symlink() or path.stat().st_size>4_000_000 or hashlib.sha256(path.read_bytes()).hexdigest()!=value:
            raise ValueError('Simulation artifact changed')
    identity=hashlib.sha256(json.dumps(manifest['source_files'],sort_keys=True).encode()).hexdigest()
    if identity!=manifest['source_version']:raise ValueError('Source identity changed')
    cfg=manifest['config'];cases=rows(folder/'cases.jsonl');results=rows(folder/'results.jsonl')
    if cfg['backend']!='simulation' or cfg['native_enabled'] or cfg['target_id'] not in cfg['allowed_target_ids']:
        raise ValueError('Invalid simulation scope')
    if not 0<len(cases)==len(results)<=cfg['max_cases']<=1000:raise ValueError('Invalid case budget or incomplete run')
    scenario=manifest['scenario']
    if scenario not in ('EXP-01-normal','EXP-02-baseline','EXP-03-defense','EXP-04-feedback-exploratory','REPLAY-single-case-baseline'):
        raise ValueError('Unknown simulation scenario')
    defended=scenario in ('EXP-03-defense','EXP-04-feedback-exploratory')
    defense,target=Defense(cfg),SimulationTarget()
    for i,(raw,result) in enumerate(zip(cases,results)):
        case=Case(**raw);now=i*cfg['logical_case_step_ms']
        decision,reason=defense.decide(case,now) if defended else ('ALLOW','baseline')
        outcome=target.send(case) if decision=='ALLOW' else dict(target_outcome='NOT_SENT',return_code=None,response_length=0)
        expected=dict(run_id=folder.name,case_id=case.case_id,source_version=identity,backend='simulation',
            scenario=scenario,target_id=cfg['target_id'],logical_time_ms=now,oracle_label=oracle(case),
            decision=decision,reason=reason,timeout=False,isolation='INCONCLUSIVE',**outcome)
        if any(result.get(key)!=value for key,value in expected.items()):raise ValueError('Simulation row contradicts replay')
    summary=summarize(results)
    if summary!=read(folder/'summary.json'):raise ValueError('Simulation summary differs from raw rows')
    return summary,manifest
