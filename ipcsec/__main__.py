import argparse
import json
from .runner import ROOT, demo, run
from .fuzzer import generate
from .evaluator import review

def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='command',required=True)
    sub.add_parser('demo')
    sub.add_parser('calibrate')
    r = sub.add_parser('replay'); r.add_argument('--case-id',required=True)
    a = p.parse_args()
    cfg = json.loads((ROOT/'configs/lab.json').read_text(encoding='utf-8'))
    if a.command == 'demo':
        for path in demo(cfg): print(path)
    elif a.command == 'replay':
        c = next((c for c in generate(min(100,cfg['max_cases']),cfg['seed']) if c.case_id == a.case_id),None)
        if c is None: p.error('case-id is not in the configured deterministic corpus')
        print(run([c],cfg,'REPLAY-single-case-baseline'))
    else:
        fixtures = json.loads((ROOT/'eval/calibration/k1-k6.json').read_text(encoding='utf-8'))
        reports = [dict(review(f),fixture_id=f['id'],expected=f['expected']) for f in fixtures]
        out = ROOT/'review/calibration-results.json'
        out.write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf-8')
        for r in reports: print(r['fixture_id'],r['status'])
        if any(r['status'] != r['expected'] for r in reports): raise SystemExit(1)
        print('Deterministic fixtures only; LLM calibration and human signoff remain pending')

if __name__ == '__main__': main()
