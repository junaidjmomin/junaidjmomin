# RAG order and evidence check

Hold the passages and question fixed, reorder the context, and check both the answer and its cited evidence. Four synthetic questions cover current policy, conflicting older text, informal commentary and insufficient evidence.

## Run

Python 3.10 or later. No dependencies or model credentials are needed for the controls.

```sh
python runner.py --seeds 7 19 42
python -m unittest -v
```

Each question has three passages. All six passage orders are evaluated in three seeded batches: 4 questions × 6 orders × 3 batches = 72 evaluations per control. Seeds shuffle the evaluation order. These deterministic controls do not become statistically independent model samples through repetition.

## Measured control results

Executed on 4 October 2026. CSV rows include each passage order, answer, citation and verdict.

| Deterministic toy control | Runs | Exact answers | Citation text supports answer | Citation is current and authoritative | Answer consistency |
|---|---:|---:|---:|---:|---:|
| First matching passage | 72 | 25.0% | 100.0% | 25.0% | 37.5% |
| Current authoritative evidence first | 72 | 100.0% | 75.0% | 75.0% | 100.0% |

A citation can support an incorrect answer when it points to an outdated policy. The first-match control demonstrates this directly: every answer matches the cited text, but only 25% answer the current question correctly. The evidence-first control correctly abstains on one of four questions, so its citation metrics are 75%, not 100%.

## Definitions

- **Exact answers:** case-insensitive match to the fixture's expected value, including an expected `unknown` abstention.
- **Citation support:** every cited ID exists and its structured value matches the answer. Answers without citations score false on this metric.
- **Current authority:** every cited passage has the requested version and is labeled authoritative.
- **Consistency:** within each question, the modal answer's frequency across orders and batches; macro-average across questions. A consistently wrong answer can score well, so this is reported alongside correctness.

The evaluator checks structured values. It does not perform semantic entailment or judge free-form prose.

## Evaluate a real pipeline

An adapter implements `respond(question, passages, seed)` and returns:

```json
{"answer": "7", "citations": ["refund-current"]}
```

Run `python runner.py --adapter your_module:respond`. Your adapter must use the supplied passage order, preserve passage IDs, and avoid consulting the expected answer. Record provider, model version, prompt, sampling settings and any API errors separately.

`http_adapter.py` supplies an optional wrapper for an endpoint you control:

```sh
RAG_EVAL_ENDPOINT=http://localhost:8000/evaluate python runner.py --adapter http_adapter:respond
```

The endpoint receives `question`, `passages` and `seed`, and must return the structured response above. `RAG_EVAL_TOKEN`, if set by you, supplies a bearer token. No HTTP or model run was performed for the included results.

## Limits

These are toy controls with explicit authority/version metadata, not LLM benchmarks or measurements of Pravaha. No real model has been evaluated. The small dataset cannot establish performance on natural documents, multilingual questions, adversarial text or semantic reasoning. Real model results and stochastic repetitions are the next experiment.
