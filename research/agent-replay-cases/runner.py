"""Offline event replay. Python 3.10+, no services or credentials required."""
import argparse
import csv
import json
from pathlib import Path


def replay(events, disabled_guard=None):
    state = {'revision': None, 'status': 'idle', 'actions': []}
    completed = set()
    required_source = None
    for event in events:
        kind = event['type']
        if kind == 'request':
            state['revision'] = event['revision']
            state['status'] = 'pending'
            required_source = event.get('source_version')
        elif kind == 'cancel':
            if event['revision'] == state['revision']:
                state['status'] = 'cancelled'
        elif kind == 'timeout':
            if event['revision'] == state['revision']:
                state['status'] = 'timed_out'
        elif kind == 'result':
            status = state['status']
            terminal = status in ('cancelled', 'timed_out')
            bypass = (disabled_guard == 'cancellation' and status == 'cancelled') or (
                disabled_guard == 'timeout' and status == 'timed_out')
            if terminal and not bypass:
                continue
            if disabled_guard != 'revision' and event['revision'] != state['revision']:
                continue
            if disabled_guard != 'deduplication' and event['call_id'] in completed:
                continue
            if required_source and disabled_guard != 'source_version' and event.get('source_version') != required_source:
                continue
            completed.add(event['call_id'])
            state['actions'].append(event['action'])
            state['status'] = 'completed'
        else:
            raise ValueError('Unknown event type: ' + kind)
    return state


def run(output):
    root = Path(__file__).resolve().parent
    cases = json.loads((root / 'cases.json').read_text())
    rows = []
    for case in cases:
        good = replay(case['events'])
        broken = replay(case['events'], case['guard'])
        rows.append({'case': case['name'], 'reference_pass': good == case['expected'],
                     'mutant_detected': broken != case['expected'],
                     'disabled_guard': case['guard']})
    output.mkdir(parents=True, exist_ok=True)
    with (output / 'results.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    traces = [{'case': c['name'], 'events': c['events'], 'expected': c['expected'],
               'reference_actual': replay(c['events']),
               'mutant_actual': replay(c['events'], c['guard'])} for c in cases]
    (output / 'traces.json').write_text(json.dumps(traces, indent=2) + '\n')
    for row in rows:
        print(f"{row['case']}: reference={row['reference_pass']}, mutant_detected={row['mutant_detected']}")
    return all(r['reference_pass'] and r['mutant_detected'] for r in rows)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parent / 'results')
    args = parser.parse_args()
    raise SystemExit(0 if run(args.output) else 1)
