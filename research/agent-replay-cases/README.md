# Replayable agent failure cases

Five offline cases check whether a late or repeated tool result produces an incorrect final action. Each fixture includes the event sequence and expected final state. A small reference state machine supplies a passing control; disabling one guard supplies a failing control.

## Run

Python 3.10 or later. No dependencies, credentials or external services.

```sh
python runner.py
python -m unittest -v
```

## Results

Executed on 4 October 2026. The full event traces and actual states are in `results/traces.json`.

| Case | Reference contract | Missing-guard implementation detected |
|---|---|---|
| Cancellation followed by a late result | Pass | Yes |
| New intent followed by an old result | Pass | Yes |
| Repeated result for the same tool call | Pass | Yes |
| Retrieval from an outdated policy version | Pass | Yes |
| Timeout followed by a late result | Pass | Yes |

The callbacks can look individually valid while producing the wrong final state. The assertions therefore inspect committed actions as well as completion status. The stale-retrieval fixture rejects an outdated result even though it belongs to the active request.

## Files and contract

- `cases.json`: readable input sequences and expected outcomes.
- `runner.py`: replay, missing-guard controls, CSV results and JSON traces.
- `test_runner.py`: contract tests plus invalid-event and unrelated-cancellation cases.
- `results/`: measured outputs from the documented run.

`revision` changes when the user changes intent. `call_id` is globally unique per logical tool operation and remains unchanged on a retry. Cancellation and timeout are terminal for that revision. Retrieval may specify an expected source version. These are explicit fixture contracts, not universal product semantics.

## Limits and next step

This is a synthetic event harness. It has not been connected to Vapi, Twilio, a real call, an LLM or a production booking system. The five missing-guard controls establish that these specific failures are detectable; they are not a coverage estimate for an agent platform. Audio timing, multiple simultaneous requests, distributed retries and compensation after an already committed action are outside the current model.

To evaluate a real agent, translate its recorded events into these fields and replace the reference replay with a wrapper that returns the agent's final state. Retain the same fixture expectations. Report real-agent results separately from the passing and failing controls.
