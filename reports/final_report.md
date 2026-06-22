# Final Report - AI Crypto Hedge Fund Research MVP

## Scope and framing

This repository is an educational historical research system for an AI-agent crypto
portfolio workflow. It is not a profitability claim, not investment advice and not an
enabled live trading bot. The MVP is long-only, unlevered, spot-only, daily-bar and
USDT-cash based.

## Final-test lock and exposure

- Final-test exposure: `EXPOSED`
- Accepted lock SHA-256: `c33b5eb396f60b1e2a7890616b8d9ae1cd69e91375dec925b68b6673d843af5e`
- Lock path: `artifacts/final_test_lock.json`
- Final-test artifact directory: `artifacts/final_test/c33b5eb396f6/`
- Final period: `2025-01-01` through `2025-12-31`
- Locked git commit: `d200df6d8a5bd1671be89ed4bb342e6a9943a1e5`
- Runner git commit: `d200df6d8a5bd1671be89ed4bb342e6a9943a1e5`
- Runner source dirty during frozen final suite: `True`
- Data hash: `9f539f38394240f5dcd922b23d234008a84a357c38ef9f2d8197acfab80d7e14`
- Validation-selected config hash: `da1dcaf442517b6c6078da6502c8bc79dabbfc2c294a704ee90d6294e72e77e8`
- Generated final config hash: `c6c79b974e7c46f4a01781fb8e2b1a96304e1c3f639a10f38fd9a0d2b1522fc6`

The final-test suite is already exposed. The report builder does not rerun final-test
experiments or alter methodology; it reads the committed frozen artifacts.

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
| Level 3 | cvar_downside | -18.0% | -0.02 | -45.2% | $1,493 | -25.4% |
| Level 4 | calendar_monthly | -4.1% | -0.88 | -9.1% | $3,584 | -9.3% |
| Level 5 | large_universe_dynamic | -28.0% | -0.22 | -42.2% | $110,939 | -45.2% |

Net after fees and slippage is primary. Several selected strategies underperformed
their benchmark in the exposed final year; those are research findings, not failures
to be hidden. The final-test evidence does not establish robust alpha.

## Level 5 proof

- Eligible pairs: `120`
- Scored pairs: `120`
- Selected holdings: `25`
- Runtime: `78.4` seconds.
- Peak RSS: `847.6` MiB.
- Proof artifact: `artifacts/final_test/c33b5eb396f6/monitoring/level_5_pair_count_proof.json`

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
| artifacts/final_test_lock.json | c33b5eb396f60b1e2a7890616b8d9ae1cd69e91375dec925b68b6673d843af5e |
| artifacts/final_test/c33b5eb396f6/final_test_suite_summary.json | f24e3fb8d126699a505db02f4227c3caf22270373a3f7fbacb59b676ba5b7ec7 |
| artifacts/final_test/c33b5eb396f6/monitoring/level_5_pair_count_proof.json | 4b31c519467703c63761b7cc3ed52d60ceef3cbb63ef208cb86500142bff2f16 |
| artifacts/final_test/c33b5eb396f6/monitoring/health_summary.csv | c65e5a5d84c8eff58ff5789ce270b07a200503dabbfa6375b0ffedb332682aa1 |
| artifacts/final_test/c33b5eb396f6/metrics/level_1.csv | 85223dfe8a87194682ec58c625af75a76192ea9fa2ddd67c4fa0aef6b83ecd00 |
| artifacts/final_test/c33b5eb396f6/metrics/level_2.csv | 619de9589dcb71a47951a165c34f6a33a5ef9c9503d7e01c2357ac43a940cc8a |
| artifacts/final_test/c33b5eb396f6/metrics/level_3.csv | 2a558c074b6b6c0fedc309e35d015ac3700688f498b72d6a22afa20f40e2b32d |
| artifacts/final_test/c33b5eb396f6/metrics/level_4.csv | b0d442da33d8762a4a35af4267ba610ab6978a79031fb057f4c7228b9c63a904 |
| artifacts/final_test/c33b5eb396f6/metrics/level_5.csv | 72df7773d50dc113b1d56f3272931eef48bd242ad12085397ec3e30d7d8f5210 |

## Command evidence

The release-facing verification commands are:

```bash
uv sync --frozen
make validate-data
make lint
make test
make notebook-full
make report
make presentation
make verify-final-lock
make pdf-page-count
make release-verify
```

After the pretest/final lock exists, `make validate-data` preserves the
lock-covered `artifacts/monitoring/level_5_data_pair_count_proof.json` hash and
writes fresh post-lock data-validation candidates only to ignored
`artifacts/monitoring/data_validation_*_latest.*` files. `make notebook-full`
executes the reviewer narrative in a clean subprocess and persists outputs in the
committed notebook; it does not rerun `make final-test`, because final-test results
are already exposed.

## Known limitations

- Active Binance/CCXT market snapshot introduces survivorship and delisting bias.
- Daily-bar volume is a liquidity/capacity proxy; no order-book depth or spread model
  is included.
- Level 5 validation 100-pair evidence has a short late-December 2024 validation
  window, though the final-test full run scored 120 pairs.
- Risk behavior can be cash-heavy under volatility and turnover constraints.
- Level 5 benchmark is a broker-costed equal-weight top-K basket, not the full
  eligible universe.
- Final-test results are exposed; this release includes only bug-fix/provenance
  reruns without changing validation-selected strategy choices.

## Publication reminder

The human owner must publish or verify the public GitHub/GitLab URL; this agent cannot
confirm repository visibility outside the local checkout.
