"""Controlled RAG evaluator. Toy baselines are fixtures, not LLM results."""
import argparse
import csv
import importlib
import itertools
import json
import random
from collections import Counter, defaultdict
from pathlib import Path


def first_match(question, passages, seed):
    for p in passages:
        if p['key'] == question['key']:
            return {'answer': p['value'], 'citations': [p['id']]}
    return {'answer': 'unknown', 'citations': []}


def evidence_first(question, passages, seed):
    eligible = [p for p in passages if p['key'] == question['key'] and p['authoritative'] and p['version'] == question['version']]
    if not eligible:
        return {'answer': 'unknown', 'citations': []}
    p = sorted(eligible, key=lambda p: p['id'])[0]
    return {'answer': p['value'], 'citations': [p['id']]}


def score(case, response):
    ids = response.get('citations', [])
    if not isinstance(ids, list) or not isinstance(response.get('answer'), str):
        raise ValueError('Adapter must return answer:string and citations:list')
    cited = {p['id']: p for p in case['passages']}
    exact = response['answer'].strip().casefold() == case['expected'].casefold()
    supported = bool(ids) and all(i in cited and cited[i]['value'].casefold() == response['answer'].strip().casefold() for i in ids)
    current = bool(ids) and all(i in cited and cited[i]['authoritative'] and cited[i]['version'] == case['question']['version'] for i in ids)
    return exact, supported, current


def evaluate(adapter, cases, seeds):
    rows = []
    for case in cases:
        permutations = list(itertools.permutations(case['passages']))
        for seed in seeds:
            random.Random(seed).shuffle(permutations)
            for index, passages in enumerate(permutations):
                response = adapter(case['question'], list(passages), seed)
                exact, supported, current = score(case, response)
                rows.append({'case': case['id'], 'seed': seed, 'order': ' '.join(p['id'] for p in passages),
                             'answer': response['answer'], 'citations': ' '.join(response.get('citations', [])),
                             'exact_match': exact, 'citation_support': supported, 'current_authority': current})
    grouped = defaultdict(list)
    for row in rows:
        grouped[row['case']].append(row['answer'].strip().casefold())
    # Per-question modal-answer frequency, then macro-average across questions.
    consistency = sum(Counter(v).most_common(1)[0][1] / len(v) for v in grouped.values()) / len(grouped)
    n = len(rows)
    summary = {'runs': n, 'exact_match': sum(r['exact_match'] for r in rows) / n,
               'citation_support': sum(r['citation_support'] for r in rows) / n,
               'current_authority': sum(r['current_authority'] for r in rows) / n,
               'answer_consistency': consistency}
    return rows, summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--adapter', help='Python module:function implementing (question, passages, seed) -> dict')
    parser.add_argument('--seeds', nargs='+', type=int, default=[7, 19, 42])
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parent / 'results')
    args = parser.parse_args()
    cases = json.loads((Path(__file__).parent / 'cases.json').read_text())
    adapters = {'first_match_toy': first_match, 'evidence_first_toy': evidence_first}
    if args.adapter:
        module, function = args.adapter.split(':', 1)
        adapters = {args.adapter: getattr(importlib.import_module(module), function)}
    args.output.mkdir(parents=True, exist_ok=True)
    summaries = {}
    for name, adapter in adapters.items():
        rows, summary = evaluate(adapter, cases, args.seeds)
        safe_name = name.replace(':', '_').replace('/', '_')
        with (args.output / (safe_name + '.csv')).open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        summaries[name] = summary
    (args.output / 'summary.json').write_text(json.dumps(summaries, indent=2) + '\n')
    print(json.dumps(summaries, indent=2))
