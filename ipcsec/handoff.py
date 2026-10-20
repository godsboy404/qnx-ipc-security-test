"""Read-only evidence audit and local source/evidence handoff packaging."""
import argparse
import hashlib
import json
import stat
import uuid
import zipfile
from datetime import datetime,timezone
from pathlib import Path,PurePosixPath,PureWindowsPath
from .native import read_json,read_rows,verify_archived,compare_policy
from .recovery import verify as verify_recovery
from .stall import verify as verify_stall

ROOT_FILES=('README.md','AGENTS.md','.gitignore','pyproject.toml')
SOURCE_DIRS=('ipcsec','native','scripts','configs','docs','eval','review','release','tests')
HISTORY_DIRS=('native-runs','native-fuzz-runs','native-recovery-runs','native-stall-runs',
              'native-comparisons','native-stall-incidents','model-review-runs','change-runs','review-runs','model-comparisons','local-check-runs')
EXTENSIONS={'.py','.ps1','.md','.json','.jsonl','.txt','.tsv','.c','.h','.sh','.csv','.log','.stderr'}
FORBIDDEN={'build','.git','.qa','__pycache__','.venv','.ssh','.aws','.codex','.agents'}
SECRET_NAMES={'.env','credentials','id_rsa','id_ed25519','qnx-lab-ed25519','ssh-ident'}


def safe_path(root,name):
    root=Path(root).resolve()
    if not isinstance(name,str) or not name or '\\' in name or ':' in name:
        raise ValueError('Expected a project-relative POSIX path')
    part=PurePosixPath(name)
    if part.is_absolute() or PureWindowsPath(name).is_absolute() or '..' in part.parts:
        raise ValueError('Path must stay inside project')
    path=(root/name).resolve()
    if path==root or not path.is_relative_to(root):raise ValueError('Path escapes project')
    return path


def digest(data):return hashlib.sha256(data).hexdigest()


def verify_embedded_evidence(files):
    """Archive checksums alone cannot detect an omitted historical dependency."""
    for name,data in files.items():
        if name.startswith('evidence/model-review-runs/') and PurePosixPath(name).name=='integrity.json':
            record=json.loads(data.decode('utf-8-sig'))
            for member,value in record['hashes'].items():
                parts=PurePosixPath(member)
                if parts.is_absolute() or '..' in parts.parts or '\\' in member or ':' in member:
                    raise ValueError('Unsafe model evidence member')
                key=str(PurePosixPath(name).parent/parts)
                if key not in files or digest(files[key])!=value:
                    raise ValueError('Missing or changed model artifact: '+key)
        if not name.startswith('evidence/') or PurePosixPath(name).name not in ('manifest.json','incident.json'):continue
        record=json.loads(data.decode('utf-8-sig'))
        hashes=record.get('evidence_hashes',record.get('hashes',{}))
        for member,value in hashes.items():
            if '/' in member or '\\' in member or member in ('.','..'):raise ValueError('Non-flat historical evidence member')
            key=str(PurePosixPath(name).parent/member)
            if key not in files or digest(files[key])!=value:raise ValueError('Missing or changed embedded evidence: '+key)


def collect_files(root):
    root=Path(root).resolve();result={}
    candidates=[root/name for name in ROOT_FILES]
    for directory in SOURCE_DIRS:
        candidates.extend((root/directory).rglob('*'))
    for directory in HISTORY_DIRS:
        candidates.extend((root/'evidence'/directory).rglob('*'))
    for summary in (root/'evidence/local-check-runs').glob('*/summary.json'):
        for name in read_json(summary).get('generated_runs',{}):
            parts=PurePosixPath(name).parts
            if len(parts)!=3 or parts[0]!='evidence' or parts[1] not in ('runs','change-runs','review-runs'):
                raise ValueError('Unexpected self-check artifact')
            candidates.extend(safe_path(root,name).rglob('*'))
    registry=root/'configs/handoff-evidence.json'
    if registry.is_file():
        for name in read_json(registry).get('simulation_paths',[]):
            part=PurePosixPath(name)
            if len(part.parts)!=3 or part.parts[:2]!=('evidence','runs'):
                raise ValueError('Only explicit simulation run folders can be selected')
            candidates.extend(safe_path(root,name).rglob('*'))
    for path in candidates:
        rel=path.relative_to(root)
        if any(part.casefold() in FORBIDDEN for part in rel.parts):continue
        if path.is_symlink():raise ValueError('Handoff excludes symlinks: '+rel.as_posix())
        if not path.is_file():continue
        if path.name.casefold() in SECRET_NAMES:continue
        if rel.as_posix() not in ROOT_FILES and path.suffix.lower() not in EXTENSIONS:continue
        safe_path(root,rel.as_posix())
        result[rel.as_posix()]=path.read_bytes()
    return dict(sorted(result.items()))


def manifest_integrity(folder,manifest):
    hashes=manifest.get('evidence_hashes',manifest.get('hashes',{}))
    if not hashes:raise ValueError('Missing evidence hashes: '+folder.name)
    for name,expected in hashes.items():
        if '/' in name or '\\' in name:raise ValueError('Evidence member must be a flat filename')
        if digest(safe_path(folder,name).read_bytes())!=expected:raise ValueError('Evidence changed: '+str(folder/name))


def verify_smoke(folder):
    manifest=read_json(folder/'manifest.json');manifest_integrity(folder,manifest)
    if manifest['backend']!='qnx-native' or manifest['run_id']!=folder.name:raise ValueError('Native smoke identity mismatch')
    if (folder/'hello.txt').read_text(encoding='utf-8-sig').strip()!='Hello QNX: course toolchain smoke test':raise ValueError('Hello output mismatch')
    for name,count,payload in [('normal.jsonl',100,4),('empty.jsonl',1,0),('restarted.jsonl',100,4)]:
        rows=read_rows(folder/name)
        if len(rows)!=count or len({r['case_id'] for r in rows})!=count:raise ValueError('Native smoke case count/identity mismatch')
        if any(r['status']!='PASS' or r['return_code']!=0 or r['backend']!='qnx-native' or r['criterion_id']!='IPC-01' or r['payload_bytes']!=payload or r['dcmd_bytes']!=16+payload or r['elapsed_ns']<0 for r in rows):raise ValueError('Native smoke request failed')
    return dict(status='PASS',isolation_verdict='INCONCLUSIVE')


def audit(root):
    root=Path(root).resolve();config=read_json(root/'configs/handoff-evidence.json')
    validators={'smoke':verify_smoke,'fuzz':verify_archived,'recovery':verify_recovery,'stall':verify_stall}
    selected=[];errors=[]
    for entry in config['selected']:
        try:
            folder=safe_path(root,entry['path'])
            result=validators[entry['kind']](folder)
            summary=result[0] if isinstance(result,tuple) else result
            manifest=read_json(folder/'manifest.json')
            code_hashes={name:value for name,value in manifest['source_hashes'].items() if name.endswith(('.c','.h','.py'))}
            matched=sum(safe_path(root,name).is_file() and digest(safe_path(root,name).read_bytes())==value for name,value in code_hashes.items())
            selected.append(dict(entry,status=summary['status'],manifest_sha256=digest((folder/'manifest.json').read_bytes()),
                historical_code_files=len(code_hashes),matching_current_code_files=matched,
                historical_code_matches_current=matched==len(code_hashes),isolation_verdict=summary['isolation_verdict']))
        except (ValueError,KeyError,OSError) as exc:
            errors.append(entry['id']+': '+str(exc))
    comparisons=[]
    for name in config['comparison_paths']:
        try:
            path=safe_path(root,name);saved=read_json(path)
            actual=compare_policy(safe_path(root,'evidence/native-fuzz-runs/'+saved['baseline_run']),
                                  safe_path(root,'evidence/native-fuzz-runs/'+saved['defense_run']))
            if actual!=saved:raise ValueError('Comparison differs from referenced runs')
            comparisons.append(dict(path=name,sha256=digest(path.read_bytes()),status='PASS'))
        except (ValueError,KeyError,OSError) as exc:errors.append(name+': '+str(exc))
    simulations=[]
    from .simulation_evidence import verify as verify_simulation
    for name in config.get('simulation_paths',[]):
        try:
            part=PurePosixPath(name)
            if len(part.parts)!=3 or part.parts[:2]!=('evidence','runs'):raise ValueError('Invalid simulation selection')
            summary,manifest=verify_simulation(safe_path(root,name))
            simulations.append(dict(path=name,status='PASS',backend='simulation',scenario=manifest['scenario'],
                source_version=manifest['source_version'],cases=summary['total'],independent_execution=False))
        except (ValueError,KeyError,OSError) as exc:errors.append(name+': '+str(exc))
    history=[]
    for directory in HISTORY_DIRS:
        for path in sorted((root/'evidence'/directory).glob('*/manifest.json')):
            try:
                manifest=read_json(path);manifest_integrity(path.parent,manifest)
                if directory=='local-check-runs':
                    from .local_check import verify as verify_local_check,verify_generated
                    verify_generated(root,verify_local_check(path.parent))
                summary_path=path.parent/'summary.json'
                if summary_path.exists():status=read_json(summary_path)['status']
                elif directory=='native-runs':status='RECORDED_LEGAL_SMOKE'
                else:status='INCOMPLETE'
                history.append(dict(path=path.parent.relative_to(root).as_posix(),recorded_status=status,integrity='PASS'))
            except (ValueError,KeyError,OSError) as exc:errors.append(str(path)+': '+str(exc))
    for path in sorted((root/'evidence/native-stall-incidents').glob('*/incident.json')):
        try:
            manifest_integrity(path.parent,read_json(path))
            history.append(dict(path=path.parent.relative_to(root).as_posix(),recorded_status='POSTMORTEM',integrity='PASS'))
        except (ValueError,KeyError,OSError) as exc:errors.append(str(path)+': '+str(exc))
    change_rehearsals=[]
    from .change_rehearsal import verify as verify_change
    for path in sorted((root/'evidence/change-runs').glob('*/manifest.json')):
        try:
            result=verify_change(path.parent)
            change_rehearsals.append(dict(path=path.parent.relative_to(root).as_posix(),
                status=result['status'],formal_E2=False,backend='simulation'))
        except (ValueError,KeyError,OSError) as exc:errors.append(str(path)+': '+str(exc))
    model_reviews=[]
    from .model_calibration import verify as verify_model_review
    for path in sorted((root/'evidence/model-review-runs').glob('*/integrity.json')):
        try:
            result=verify_model_review(path.parent)
            model_reviews.append(dict(path=path.parent.relative_to(root).as_posix(),
                technical_calibration=result['technical_calibration'],matches=result['matches'],count=result['count'],
                independent_calibration=False,human_signoff='pending',integrity='PASS'))
        except (ValueError,KeyError,OSError) as exc:errors.append(str(path)+': '+str(exc))
    return dict(schema_version=1,created_utc=datetime.now(timezone.utc).isoformat(),
        selected_evidence_status='PASS' if not errors else 'FAIL',selected=selected,comparisons=comparisons,
        history=history,nonpassing_history=[h for h in history if h['recorded_status'] in ('FAIL','INCOMPLETE')],
        model_reviews=model_reviews,change_rehearsals=change_rehearsals,simulations=simulations,
        course_gate='PENDING',peer_reproduced=False,pending=config['pending'],errors=errors,
        version_note='Current source snapshot is included. Historical manifests identify their own versions; differing historical source is not reconstructed.')


def write_bundle(root,report,files):
    """Write a new immutable local draft; no external publication or Git changes."""
    root=Path(root).resolve()
    if report['selected_evidence_status']!='PASS':raise ValueError('Cannot package failed selected evidence')
    verify_embedded_evidence(files)
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    dest=root/'build/handoff'/run_id;dest.mkdir(parents=True,exist_ok=False)
    snapshot={name:digest(data) for name,data in files.items() if not name.startswith('evidence/')}
    report_data=json.dumps(report,indent=2,ensure_ascii=False).encode('utf-8')
    snapshot_data=json.dumps(dict(source_hashes=snapshot,identity='per-file SHA256; includes current uncommitted files'),indent=2).encode('utf-8')
    content=dict(files);content['HANDOFF-AUDIT.json']=report_data;content['SOURCE-SNAPSHOT.json']=snapshot_data
    package_manifest=dict(schema_version=1,status='LOCAL_HANDOFF_DRAFT',course_gate='PENDING',
        peer_reproduced=False,files={name:digest(data) for name,data in sorted(content.items())},
        excluded='VM/SDK/binaries/SSH keys/build/.git/private runtime directories',
        historical_failures_preserved=True)
    archive=dest/'qnx-ipc-security-test-handoff.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as out:
        for name,data in sorted(content.items()):out.writestr('qnx-ipc-security-test/'+name,data)
        out.writestr('qnx-ipc-security-test/PACKAGE-MANIFEST.json',json.dumps(package_manifest,indent=2))
    (dest/'handoff-audit.json').write_bytes(report_data)
    (dest/'source-snapshot.json').write_bytes(snapshot_data)
    (dest/'SHA256SUMS.txt').write_text(''.join(f'{digest(path.read_bytes())}  {path.name}\n' for path in (archive,dest/'handoff-audit.json',dest/'source-snapshot.json')),encoding='ascii')
    verify_bundle(archive)
    return dest


def verify_bundle(path):
    with zipfile.ZipFile(path) as archive:
        names=archive.namelist();prefix='qnx-ipc-security-test/'
        if len(names)!=len(set(names)):raise ValueError('Duplicate archive entries')
        manifest= json.loads(archive.read(prefix+'PACKAGE-MANIFEST.json'))
        expected={prefix+name for name in manifest['files']}|{prefix+'PACKAGE-MANIFEST.json'}
        if set(names)!=expected:raise ValueError('Archive member set mismatch')
        for name,value in manifest['files'].items():
            parts=PurePosixPath(name)
            if parts.is_absolute() or '..' in parts.parts or '\\' in name or ':' in name or any(p.casefold() in FORBIDDEN for p in parts.parts):raise ValueError('Unsafe archive member')
            info=archive.getinfo(prefix+name)
            if stat.S_ISLNK(info.external_attr>>16) or digest(archive.read(info))!=value:raise ValueError('Archive integrity failed: '+name)
        if manifest['course_gate']!='PENDING' or manifest['peer_reproduced'] is not False:raise ValueError('Unsupported signoff claim')
        verify_embedded_evidence({name:archive.read(prefix+name) for name in manifest['files']})
    return len(manifest['files'])


def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('audit','package','verify-bundle'))
    parser.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));parser.add_argument('--archive')
    args=parser.parse_args()
    if args.action=='verify-bundle':print('Verified files:',verify_bundle(args.archive));return
    report=audit(args.root)
    if args.action=='audit':print(json.dumps(report,indent=2,ensure_ascii=False))
    else:print(write_bundle(args.root,report,collect_files(args.root)))
    if report['errors']:raise SystemExit(1)

if __name__=='__main__':main()
