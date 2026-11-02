# Wintermancer™ 20-Case Agent Tool-Calling Evaluation & Defect Repair Harness

Reproducible open-source evaluation harness (`MIT` License) demonstrating deterministic detection and pre-execution guardrail repair of **ungrounded mutating tool-argument execution** in customer-support and workflow agents.

- **Fixed-Scope `$750.00` 20-Case Agent Evaluation and Defect Repair Service:** https://snowfieldhq.neocities.org/wintermancer-eval-repair.html (`1 engagement * $750.00 = $750.00` gross; `$750.00 - ($750.00 * 0.033 + $0.30) = $724.95` net after standard card processing)
- **GitHub Pages Mirror:** https://snowfieldhq.github.io/wintermancer-eval-repair.html
- **`$0.00` Downloadable Archive on itch.io:** https://wintermancer.itch.io/20-case-agent-eval-sample
- **Direct Engineering Intake:** `snowfieldhq+wintermancer@atomicmail.io`

---

## Verified Benchmark Summary (`0.05` Seconds Offline Execution)

| Scenario Group | Failure Pattern Tested | Baseline Pass Rate | Baseline Silent Wrong Mutations | Repaired Pass Rate | Repaired Wrong Mutations |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Ambiguous Multi-Record Target (`TC-01` to `TC-05`)** | Guesses newest order, first SKU, or immediate plan timing when `2+` records exist | `0 / 5` | `5` | **`5 / 5`** | **`0`** |
| **Amount, Unit & Address Coercion (`TC-06` to `TC-10`)** | Refunds full order for shipping-only ask, `$20` as `20` cents, `>$100` cap, stale postal code | `1 / 5` | `4` | **`5 / 5`** | **`0`** |
| **Intent & Ownership Boundary (`TC-11` to `TC-15`)** | Executes live mutations on hypothetical policy questions, status checks, or coworker order IDs | `0 / 5` | `5` | **`5 / 5`** | **`0`** |
| **Valid Regression Controls (`TC-16` to `TC-20`)** | Unambiguous refunds, replacement reshipment, plan upgrade, and status lookup | `5 / 5` | `0` | **`5 / 5`** | **`0`** |
| **Total Across 20 Cases** | Deterministic runner (`run_eval.py --verify`) + Promptfoo assertion bridge | **`6 / 20` (`30.0%`)** | **`14` wrong calls** | **`20 / 20` (`100.0%`)** | **`0` wrong calls** |

In ablation testing against raw unrepaired baseline model turns, the deterministic pre-execution guardrail (`guardrail.py`) alone blocks **`14 / 14`** unauthorized mutating tool calls (`0` silent side effects).

---

## Quick Start (Zero External Dependencies)

```bash
python guardrail.py
python run_eval.py --verify
```

Expected console verification output:

```text
Guardrail self-tests passed.
Dataset SHA-256: 35d9cb44e657be87... | Baseline: 6/20 (30.0%, 14 wrong mutating calls) -> Repaired: 20/20 (100.0%, 0 wrong mutating calls)
```

## Repository Contents

- `run_eval.py`: Deterministic evaluation runner grading baseline turns, guardrail ablation, and repaired turns across all 20 scenarios.
- `guardrail.py`: Pre-execution argument verifier enforcing session record ownership, unique record disambiguation, authorized monetary bounds, and postal-code provenance.
- `cases.json` (and `cases_20.json`): 20 synthetic customer-support tool-calling test cases (`ParcelDesk Support Agent`).
- `prompts/` & `schemas/`: Baseline vs. repaired system prompts and JSON tool schemas (`ask_clarification`, `amount_basis`, and `user_intent_quote`).
- `results/`: Reproducible JSON outputs (`summary.json`, `baseline_run.json`, `repaired_run.json`, `promptfoo_tests.json`).
- `eval-repair-demonstration.pdf`: 2-page visual engineering proof and 20-case ledger.
- `promptfooconfig.yaml` & `promptfoo_assert.py`: Ready-to-run [Promptfoo](https://github.com/promptfoo/promptfoo) live-provider configuration (`npx promptfoo@latest eval -c promptfooconfig.yaml`).

## Scope & Non-Certification Notice

All records in `cases.json` are synthetic fixtures. Passing `20 / 20` verifies reproduction (`6 / 20` baseline) and repair (`20 / 20` rerun, `5 / 5` valid controls preserved) for this single defined defect class. Twenty cases never certify an application as safe, aligned, or secure overall.
