# Final Report - AI Crypto Hedge Fund Research MVP

## Scope and framing

This repository is an educational historical research system for an AI-agent crypto
portfolio workflow. It is not a profitability claim, not investment advice and not an
enabled live trading bot. The MVP is long-only, unlevered, spot-only, daily-bar and
USDT-cash based.

## Final-test lock and exposure

- Final-test exposure: `EXPOSED`
- Accepted lock SHA-256: `dab407601cbaf8198361e5e3d074260546ed4bbab4c4be2555248b246631308b`
- Lock path: `artifacts/final_test_lock.json`
- Final-test artifact directory: `artifacts/final_test/dab407601cba/`
- Final period: `2025-01-01` through `2025-12-31`
- Locked git commit: `394d146523445ed53c978ade1033cc7870237a8f`
- Runner git commit: `6aad82116feb26f83b7658414207e03371e07864`
- Runner source dirty during Stage 11 final suite: `True`
- Data hash: `9f539f38394240f5dcd922b23d234008a84a357c38ef9f2d8197acfab80d7e14`
- Validation-selected config hash: `3f2dd08bbec595d6233852bfc94de6eae0a2cdb91d6aeec1f408afbbd10046cf`
- Generated final config hash: `c6c79b974e7c46f4a01781fb8e2b1a96304e1c3f639a10f38fd9a0d2b1522fc6`

The final-test suite is already exposed. Stage 12 did not rerun final-test experiments
or alter methodology; it reads committed Stage 11 artifacts.

## Data, execution and costs

- Timestamp convention: daily bars are UTC bar-start records; completed-bar features
  execute at the next available open.
- Cost convention: fee-bearing notional is risky-asset notional actually traded.
- One-way fee: `10.0` bps.
- One-way slippage: `5.0` bps.
- Initial capital: `$1,000,000`.
- Risk-free rate: `0.0`.

## Final-test selected results

| Level | Selected result | Net return | Net Sharpe | Max drawdown | Total costs | Benchmark |
| --- | --- | --- | --- | --- | --- | --- |
| Level 1 | SMA baseline | -7.4% | -0.17 | -18.5% | $8,906 | -5.4% |
| Level 2 | agent_ensemble | -0.6% | -0.52 | -1.4% | $1,600 | -5.4% |
| Level 3 | cvar_downside | -18.0% | -0.02 | -45.2% | $1,492 | -25.4% |
| Level 4 | calendar_monthly | -4.1% | -0.88 | -9.1% | $3,584 | -9.3% |
| Level 5 | large_universe_dynamic | -28.0% | -0.22 | -42.2% | $110,939 | -5.4% |

Net after fees and slippage is primary. Several selected strategies underperformed
their benchmark in the exposed final year; those are research findings, not failures
to be hidden.

## Level 5 proof

- Eligible pairs: `120`
- Scored pairs: `120`
- Selected holdings: `25`
- Runtime: `75.2` seconds.
- Peak RSS: `727.3` MiB.
- Proof artifact: `artifacts/final_test/dab407601cba/monitoring/level_5_pair_count_proof.json`

## Agent interaction trace

The notebook displays a readable Level 2 trace from agent outputs to aggregate signal,
portfolio proposal and risk approval. The committed trace shows SMA, econometric,
logistic-regression and gradient-boosting agents emitting typed scores/confidence with
cutoffs and reason codes. The aggregate signal was negative for BTC/USDT on the shown
decision, so the approved portfolio was cash with reason code `ok`.

## Monitoring and fail-safes

The final Level 5 health summary reports system status
`ok`, eligible/scored count ranges
`100`-`120`,
and `53` monitoring incidents.
Demonstrated fail-safe scenarios include
`["kill_switch_cash_schedule_unit_test", "volatility_limit_cash_approval", "invalid_feature_alert_path", "weight_reconciliation_post_risk"]`.

## Artifact hashes

| Artifact | SHA-256 |
| --- | --- |
| artifacts/final_test_lock.json | dab407601cbaf8198361e5e3d074260546ed4bbab4c4be2555248b246631308b |
| artifacts/final_test/dab407601cba/final_test_suite_summary.json | 759e6051f243f5ef2bb5aacaeaa7c5f1a5158f153d71b05cd3ad9cd49d0adf1e |
| artifacts/final_test/dab407601cba/monitoring/level_5_pair_count_proof.json | df01221bb763ebbf5c20b50158716d4130ea1dff4b233f3b76248f5708278f93 |
| artifacts/final_test/dab407601cba/monitoring/health_summary.csv | 995eaf5b4107b7580cbd5773d30571c1532646086423f3c18302ec6db4602e5f |
| artifacts/final_test/dab407601cba/metrics/level_1.csv | b9085ec8cac78d2c0d1e25d71d07f74b095cf2a72409f04d597a100901d92886 |
| artifacts/final_test/dab407601cba/metrics/level_2.csv | d45ce4a931d6d1319b1c6da7441dbc6286c980f7fc8abe50b246df037e3b65b1 |
| artifacts/final_test/dab407601cba/metrics/level_3.csv | c0ec6ccceb579f7ff54dc392bd203be82061986428e930be8e4f3eeac44b2672 |
| artifacts/final_test/dab407601cba/metrics/level_4.csv | 065e8f4244fe1ccfccc8955351b0de21be82ee4865fe053fb72f54d8703a74e6 |
| artifacts/final_test/dab407601cba/metrics/level_5.csv | 86a11b90ba78398132ba4e91fe19eab9be509f2dae6ade6ee8e034d515f18495 |

## Command evidence

The Stage 12 implementation report contains exact command logs for the required
verification commands. Reviewer-facing commands are:

```bash
uv sync --frozen
make lint
make test
make notebook-fast
make notebook-full
make report
make presentation
```

## Known limitations

- Active Binance/CCXT market snapshot introduces survivorship and delisting bias.
- Daily-bar volume is a liquidity/capacity proxy; no order-book depth or spread model
  is included.
- Level 5 validation 100-pair evidence has a short late-December 2024 validation
  window, though the final-test full run scored 120 pairs.
- Risk behavior can be cash-heavy under volatility and turnover constraints.
- Level 5 benchmark is BTC-normalized, not a fully investable equal-weight dynamic
  benchmark.
- Stage 11 final artifacts record dirty runner-source provenance because the frozen
  final suite was run before committing the runner implementation and broker defect fix.

## Publication reminder

The human owner must publish or verify the public GitHub/GitLab URL; this agent cannot
confirm repository visibility outside the local checkout.
