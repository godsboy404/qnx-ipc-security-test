"""OBS-01: host-owned registry -> verified local archive -> bounded schema-v2 packet.

No target code execution, arbitrary file access, shell, URL or test-registration tool.
The registry is project-owned, not a teacher approval or a cryptographic signature.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
from .native import verify_archived
from .semantic_review import canonical, identity
from .review_contract_v2 import sha_text, validate_packet

TRUSTED_ROOT=Path(__file__).resolve().parents[1]
REGISTRY='configs/review-registry.json'


def bounded_file(root,name,limit=4_000_000):
    if not isinstance(name,str) or not name or '\\' in name or ':' in name:
        raise ValueError('Project-relative POSIX path required')
    parts=PurePosixPath(name)
    if parts.is_absolute() or '..' in parts.parts:raise ValueError('Path escape')
    root=Path(root).resolve();current=root
    for part in parts.parts:
        current=current/part
        if current.is_symlink() or getattr(current,'is_junction',lambda:False)():
            raise ValueError('Links/junctions are not accepted as registered evidence')
    path=current.resolve()
    if not path.is_relative_to(root) or not path.is_file() or path.stat().st_size>limit:
        raise ValueError('Missing, escaped or oversized registered file')
    return path


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))


def build_packet(release_id,criterion_id,root=None):
    root=Path(root) if root is not None else TRUSTED_ROOT
    path=bounded_file(root,REGISTRY,200_000);registry=read(path)
    if set(registry)!={'schema_version','contract','releases'} or registry['schema_version']!=2:
        raise ValueError('Invalid host registry')
    contract=registry['contract']
    if set(contract)!={'id','path','sha256','status'} or contract['status']!='project_draft':
        raise ValueError('Teacher approval is not configured; project contract remains draft')
    if contract['path']!='docs/specification.md':raise ValueError('Unregistered contract path')
    spec=bounded_file(root,contract['path'],200_000)
    if digest(spec)!=contract['sha256']:raise ValueError('Contract changed; review and repin registry first')
    entry=registry['releases'].get(release_id)
    if not entry or set(entry)!={'path','manifest_sha256','source_version','criteria'}:
        raise ValueError('Unknown release or invalid registry entry')
    if criterion_id not in entry['criteria'] or criterion_id not in ('SEC-03','OBS-01','ISO-01'):
        raise ValueError('Criterion not registered for release')
    folder_name=PurePosixPath(entry['path'])
    if len(folder_name.parts)!=3 or folder_name.parts[:2]!=('evidence','native-fuzz-runs'):
        raise ValueError('Only pinned native fuzz archives are currently supported')
    manifest_path=bounded_file(root,entry['path']+'/manifest.json',500_000)
    if digest(manifest_path)!=entry['manifest_sha256']:raise ValueError('Registered manifest changed')
    manifest=read(manifest_path)
    if identity(manifest['source_hashes'])!=entry['source_version']:raise ValueError('Source identity mismatch')
    if manifest.get('backend')!='qnx-native':raise ValueError('Not a native archive')
    for member in manifest['evidence_hashes']:
        if PurePosixPath(member).name!=member:raise ValueError('Non-flat archive member')
        bounded_file(root,entry['path']+'/'+member)
    # Recompute raw-log semantics, not just the presence of a summary or its hash.
    summary,checked_manifest=verify_archived(manifest_path.parent)
    if checked_manifest!=manifest:raise ValueError('Archive changed during preflight')
    verification=dict(run_id=manifest['run_id'],manifest_sha256=digest(manifest_path),
        evidence_member_count=len(manifest['evidence_hashes']),
        evidence_hash_mapping_sha256=identity(manifest['evidence_hashes']),
        raw_log_reanalysis_matches_summary=True,
        note='Local archive reanalysis only, no independent QNX rerun, peer signature or authenticity claim.')
    excerpts=[('archived-native-summary',summary,'qnx_native','target_runner'),
              ('local-native-reverification',verification,'host','static_inspection')]
    evidence=[]
    for name,value,backend,source in excerpts:
        text=canonical(value).decode('utf-8')
        evidence.append(dict(id=name,source_version=entry['source_version'],backend=backend,
            evidence_source=source,verification_level='OBSERVED',excerpt=text,excerpt_sha256=sha_text(text)))
    packet=dict(schema_version=2,criterion_id=criterion_id,scope=entry['criteria'][criterion_id],
        source_version=entry['source_version'],input_kind='registered_archive',registry_id=release_id,
        registry_sha256=digest(path),contract={k:contract[k] for k in ('id','status','sha256')},
        evidence=evidence,excluded_evidence=[],approved_na=False,na_approval_id=None,complete_system_probes=False)
    validate_packet(packet)
    return packet


def assert_registered_packet(packet):
    expected=build_packet(packet['registry_id'],packet['criterion_id'])
    if expected!=packet:raise ValueError('Packet differs from current trusted registry and verified archive')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release',required=True)
    parser.add_argument('--criterion',choices=('SEC-03','OBS-01','ISO-01'),required=True)
    parser.add_argument('--out',required=True,help='New packet path; local preflight only, no network')
    args=parser.parse_args()
    packet=build_packet(args.release,args.criterion)
    with Path(args.out).open('x',encoding='utf-8') as stream:json.dump(packet,stream,ensure_ascii=False,indent=2)
    print('Local preflight PASS; no model call; contract authority:',packet['contract']['status'])


if __name__=='__main__':main()
