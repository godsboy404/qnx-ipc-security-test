"""Prepare registered, locally revalidated schema-v2 review snapshots. No network."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ipcsec.registered_review import build_packet
from ipcsec.model_calibration import prepare

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--folder',required=True,help='New dedicated snapshot directory')
parser.add_argument('--release',default='defense-20261017')
args=parser.parse_args()
cases={f'REAL-{criterion}':build_packet(args.release,criterion)
       for criterion in ('SEC-03','OBS-01','ISO-01')}
answers={name:dict(expected='INSUFFICIENT_EVIDENCE' if name=='REAL-ISO-01' else 'PASS',
    oracle_author='AI-authored limited interpretation of locally verified evidence; independent review pending')
    for name in cases}
print(prepare(Path(args.folder),cases,answers))
