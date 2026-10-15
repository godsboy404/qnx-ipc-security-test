import hashlib
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
from .model import Case
from .fuzzer import generate, FeedbackScheduler
from .defense import Defense
from .harness import SimulationTarget
from .monitor import isolation_verdict, unknown_probes
from .metrics import summarize

ROOT = Path(__file__).resolve().parent.parent

def source_identity():
    paths = []
    for folder in ('ipcsec','configs','eval','native','tests','scripts','docs'):
        paths.extend(p for p in (ROOT/folder).rglob('*') if p.is_file()
                     and '__pycache__' not in p.parts and p.suffix not in ('.docx','.png','.pdf'))
    paths.extend(ROOT/p for p in ('README.md','AGENTS.md','pyproject.toml'))
    records = {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
    digest = hashlib.sha256(json.dumps(records,sort_keys=True).encode()).hexdigest()
    return digest, records

def oracle(c):
    # Independent contract oracle; never call the defense decision to derive truth labels.
    if c.operation != 'ECHO' or c.flags != 0: return 'invalid'
    size = len(bytes.fromhex(c.payload_hex))
    return 'valid' if 0 <= c.offset <= size and 0 <= c.declared_length <= 64 and c.declared_length == size else 'invalid'

def run(cases, cfg, scenario, defended=False, feedback=False):
    if cfg['backend'] != 'simulation' or cfg['native_enabled']:
        raise ValueError('Only explicit simulation backend is currently implemented')
    if cfg['target_id'] not in cfg['allowed_target_ids']:
        raise PermissionError('Target not registered; no execution')
    if not 0 < len(cases) <= cfg['max_cases'] <= 1000:
        raise ValueError('Case budget exceeded or invalid')
    version, files = source_identity()
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    dest = ROOT/'evidence'/'runs'/run_id
    dest.mkdir(parents=True, exist_ok=False)
    target, defense = SimulationTarget(), Defense(cfg)
    scheduler = FeedbackScheduler(cases)
    rows, executed, previous = [], [], None
    for i in range(len(cases)):
        c = scheduler.next(previous if feedback else None)
        decision, reason = defense.decide(c, i*cfg['logical_case_step_ms']) if defended else ('ALLOW','baseline')
        result = target.send(c) if decision == 'ALLOW' else {'target_outcome':'NOT_SENT','return_code':None,'response_length':0}
        row = {'run_id':run_id,'case_id':c.case_id,'backend':'simulation', 'source_version':version,
               'scenario':scenario,'target_id':cfg['target_id'],'logical_time_ms':i*cfg['logical_case_step_ms'],
               'oracle_label':oracle(c),'decision':decision,'reason':reason,**result,
               'timeout':False,'probe_source':'unavailable','probes':unknown_probes(),
               'isolation':isolation_verdict(unknown_probes())}
        rows.append(row); executed.append(c.record()); previous = row
    for name, data in (('cases.jsonl',executed),('results.jsonl',rows)):
        (dest/name).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in data),encoding='utf-8')
    (dest/'summary.json').write_text(json.dumps(summarize(rows),indent=2),encoding='utf-8')
    evidence = {n:hashlib.sha256((dest/n).read_bytes()).hexdigest() for n in ('cases.jsonl','results.jsonl','summary.json')}
    manifest = {'run_id':run_id,'source_version':version,'source_files':files,'spec_version':'draft-0.1',
                'config':cfg,'scenario':scenario,'backend':'simulation','evidence_source':'local_simulation_runner',
                'evidence_hashes':evidence,'hash_limit':'integrity only; not independent execution proof',
                'human_signoff':'pending','qnx_verified':False}
    (dest/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    return dest

def demo(cfg):
    count = min(100,cfg['max_cases'])
    normal = [Case(f'NORMAL-{i:04d}') for i in range(count)]
    corpus = generate(count,cfg['seed'])
    return [run(normal,cfg,'EXP-01-normal'),run(corpus,cfg,'EXP-02-baseline'),
            run(corpus,cfg,'EXP-03-defense',True),run(corpus,cfg,'EXP-04-feedback-exploratory',True,True)]
