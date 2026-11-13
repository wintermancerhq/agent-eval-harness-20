# Agent tool-calling evaluation example

A reproducible, offline example of testing one failure class in a fictional customer-support workflow. The included synthetic cases cover ambiguous records, policy limits, record ownership, hypothetical requests and valid controls.

This repository is part of Jordan Masopust's independent project work at Snowfield LLC, hosted under Snowfield's wintermancerhq GitHub organization. It was prepared with artificial intelligence assistance.

## Run the example

```sh
python guardrail.py
python run_eval.py --verify
```

The checked-in deterministic baseline passes 6 of 20 cases; the repaired fixture set passes 20 of 20. The verifier blocks 14 of 14 unauthorized mutating calls in the saved baseline. These are fixture-reproduction results, not a new live-model evaluation or evidence of production performance. Run the commands to reproduce the current repository state.

## Files

- `cases.json` and `cases_20.json`: synthetic support cases.
- `run_eval.py` and `guardrail.py`: deterministic scoring and argument checks.
- `prompts/` and `schemas/`: prompt and tool-schema examples.
- `results/`: saved outputs.
- `promptfooconfig.yaml` and `promptfoo_assert.py`: a separate live-provider evaluation configuration; its results depend on the chosen provider and run.

## Limits

Twenty cases cover one defined defect class. They do not establish that an application is safe, secure or reliable overall. All customer records here are fictional. No paid customer or production deployment result is claimed.

MIT license; see LICENSE.
