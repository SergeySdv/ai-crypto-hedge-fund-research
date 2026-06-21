# Stage 14 Quant / Model / Notebook QA

Reviewer: D
Scope: report-only independent quant/model/notebook QA. No final-test rerun.
Recommendation: **PASS_WITH_NOTES**

## Sources

- `AGENTS.md`
- `PROJECT_TASK.md`
- `docs/STAGE_14_FINALIZATION_TEAMLEAD_PROMPT.md`
- Required architecture/protocol docs `docs/00`, `11`, `01`, `02`, `03`, `04`, `09`, `05`, `06`, `12`, `07`, `10`
- Source: `src/crypto_hedge_fund/features/level2.py`, `src/crypto_hedge_fund/models/ml.py`, `src/crypto_hedge_fund/models/econometric.py`, `src/crypto_hedge_fund/experiments/level_2.py`, `src/crypto_hedge_fund/features/level5.py`, `src/crypto_hedge_fund/experiments/level_5.py`
- Evidence: `reports/final_report.md`, `notebooks/ai_crypto_hedge_fund.ipynb`, `presentation/deck.md`, `presentation/deck.pdf`, `artifacts/metrics/level_2.csv`, `artifacts/monitoring/level_2_robustness.json`, `artifacts/monitoring/level_2_fit_audit.parquet`, `artifacts/final_test/dab407601cba/**`

## Files Inspected

- `configs/default.yaml`
- `configs/validation_selected.yaml`
- `artifacts/final_test_lock.json`
- `artifacts/final_test/dab407601cba/final_test_suite_summary.json`
- `artifacts/final_test/dab407601cba/final_test_exposure_evidence.json`
- `artifacts/final_test/dab407601cba/metrics/level_{1..5}.csv`
- `artifacts/final_test/dab407601cba/monitoring/level_5_pair_count_proof.json`
- `artifacts/final_test/dab407601cba/{orders,fills,weights}/level_5.parquet`
- `reports/stage_14/final_test_suite_summary_portable.json`

## Commands

| Command / probe | Status | Notes |
| --- | --- | --- |
| `sed` required docs and source files | PASS | Read required instructions and relevant source. |
| `rg` over notebook/report/deck/model context | PASS | Checked wording around ML, Level 5, alpha, leakage, selection. |
| Python notebook JSON probe | PASS | 29 cells, 14 executed code cells, no empty code outputs. |
| Python pandas artifact probes | PASS | Read metrics, robustness, fit-audit and Level 5 economics. |
| PDF page-count regex probe | PASS | `presentation/deck.pdf` has 10 pages. |
| `git status --short`, `git diff --cached` | PASS | Read-only; found staged frozen JSON modifications. |
| `git diff --quiet stage/13-clean-clone-release -- artifacts/final_test/dab407601cba/final_test_suite_summary.json artifacts/final_test/dab407601cba/final_test_exposure_evidence.json` | PASS | Exit `0`; current working-tree bytes match Stage 13 for frozen JSON. |
| `shasum -a 256 artifacts/final_test/dab407601cba/final_test_suite_summary.json artifacts/final_test/dab407601cba/final_test_exposure_evidence.json` | PASS | Summary `759e6051...`; evidence `058f2ace...`. |
| `shasum -a 256 reports/stage_14/final_test_suite_summary_portable.json` | PASS | Portable derived summary hash `c6dc10dd...`. |
| `rg` deck/template remediation terms | PASS | `pooled scoring` absent; deterministic cross-sectional scoring and robust-alpha caveat present. |
| `git status --short reports/stage14_model_transparency_context.md` | PASS | Old out-of-scope tracked model transparency report is deleted in the candidate. |
| `make final-test` | NOT RUN | Explicitly prohibited and not run. |
| `make notebook-full/report/presentation` | NOT RUN | Not needed for this report; existing executed artifacts inspected. |

## Findings

### High

None open.

### Medium

None open.

### Resolved on Re-review

1. **Frozen final-test summary/evidence preservation: resolved.**

   Re-review confirmed `git diff --quiet stage/13-clean-clone-release -- artifacts/final_test/dab407601cba/final_test_suite_summary.json artifacts/final_test/dab407601cba/final_test_exposure_evidence.json` exits `0`. Current hashes are:
   - `final_test_suite_summary.json`: `759e6051f243f5ef2bb5aacaeaa7c5f1a5158f153d71b05cd3ad9cd49d0adf1e`
   - `final_test_exposure_evidence.json`: `058f2aceb78d35b22e958c7145c382186e34fc41282f0fb07beea8bddacad88f`

   The staged diff is a restoration back to the Stage 13 frozen provenance bytes, not a new mutation away from the accepted state. The remaining absolute `/Users/...` strings are frozen provenance strings explicitly allowed by the Stage 14 prompt when preserved byte-for-byte and paired with a separate portable view. That portable view exists at `reports/stage_14/final_test_suite_summary_portable.json` and records the source frozen artifact and hash.

2. **Deck Level 5 wording: resolved.**

   `presentation/deck.md` and `src/crypto_hedge_fund/reporting/builders.py` now use “deterministic cross-sectional scoring agents”; `pooled scoring` is absent from the checked deck/template surfaces.

3. **Deck robust-alpha caveat: resolved.**

   `presentation/deck.md` now explicitly states that final-test results did not establish robust alpha. `presentation/deck.pdf` remains at 10 pages.

4. **Out-of-scope old model transparency report removal: resolved.**

   `reports/stage14_model_transparency_context.md` is deleted in the candidate. This is consistent with the Stage 14 bounded-reporting instruction to keep reviewer reports under `reports/stage_14/` rather than maintaining adjacent historical working notes.

### Low / Notes

5. **Level 2 source and reviewer-facing model claims match.**

   Verified 20 causal features in `LEVEL2_FEATURE_COLUMNS`; target is `open(t+2)/open(t+1)-1 > threshold_return`; default threshold is `0.0020`; ML uses monthly expanding walk-forward; econometric uses daily causal expanding refit; seeds are `[7, 42, 137]`; primary persisted predictions use the first seed.

6. **Level 2 ML classes and hyperparameters match the claims.**

   `ml_logistic`: `SimpleImputer(strategy="median") -> StandardScaler() -> LogisticRegression(max_iter=500, random_state=seed, class_weight="balanced")`.
   `ml_hist_gradient_boosting`: `SimpleImputer(strategy="median") -> HistGradientBoostingClassifier(max_iter=60, learning_rate=0.05, max_leaf_nodes=15, random_state=seed, l2_regularization=0.01)`.

7. **Future-label/leakage evidence is represented accurately.**

   Validation fit audit: 2555 rows, 0 future-label flags. Final-test fit audit: 2548 rows, 0 future-label flags. Cadences are `daily_causal` for econometric and `monthly` for ML.

8. **Level 2 selection honesty is acceptable.**

   Validation table shows `agent_ensemble` selected despite not having the highest validation return or Sharpe. Notebook/report describe it as the representative multi-agent candidate, not as the numerical winner.

9. **Robustness evidence is accurately described as inconclusive.**

   Existing artifact reports moving-block bootstrap 1000 reps, block length 14, Sharpe CI `[-1.049, 3.020]`; circular shift 1000 reps, observed correlation `-0.0177`, p-value `0.6823`. Notebook/report correctly avoid significant-alpha claims.

10. **Level 5 is correctly implemented and mostly described as deterministic scoring, not fitted ML.**

   Source uses deterministic z-scored blend of 20/60-day momentum, 60-day volatility penalty, liquidity, drawdown and history confidence; no fitted Level 5 classifier/regressor found. Final artifacts show 120 eligible, 120 scored, 25 selected.

11. **Final results and limitations are honest in report/notebook.**

   Selected final net returns: L1 `-7.44%`, L2 `-0.60%`, L3 `-17.98%`, L4 `-4.05%`, L5 `-27.99%`. The final report and notebook disclose negative/inconclusive results and post-exposure alternatives without reselecting.

12. **Level 5 economic diagnosis matches artifacts.**

   Final artifacts show 364 submitted rebalances, 8727 fills, about `$73.96M` fee-bearing order notional, `$110,938.85` total costs, turnover `49.24`, 52 full-cash days, average risky exposure `85.35%`, average cash `14.65%`.

13. **Notebook is a genuine technical demonstration.**

   It imports package functions, builds Level 2 features/target from included pre-2025 data, loads fit audits and robustness artifacts, loads frozen final artifacts as evidence only, and computes Level 5 economics from parquet files. It is not merely a prose wrapper.

14. **Deck page count passes.**

   `presentation/deck.pdf` page-count probe returns `10`.

## Recommendation

**PASS_WITH_NOTES** for the quant/model/notebook reviewer scope. The model claims, validation-selection narrative, robustness interpretation, final-result limitations, Level 5 deterministic-scoring framing, notebook demonstration, and deck page count are now acceptable. Remaining notes are non-blocking: frozen Stage 11 JSON retains disclosed absolute local provenance strings by design, and public-release acceptance should still ensure the portable summary is the reviewer-facing artifact used for clean-clone/path portability.
