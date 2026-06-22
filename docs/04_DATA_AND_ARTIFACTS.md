# Data And Artifacts

## Frozen Data Snapshot

The default run uses included frozen data:

| File | Purpose |
| --- | --- |
| `data/processed/ohlcv_daily.parquet` | daily OHLCV panel |
| `data/processed/instruments.parquet` | instrument metadata |
| `data/manifests/ohlcv_daily_manifest.json` | source, parameters, hashes, coverage |

Snapshot summary:

- Source: Binance spot via CCXT public OHLCV.
- Quote currency: USDT.
- Frequency: daily bars.
- Date range: 2021-01-01 through 2025-12-31 UTC where available.
- Rows: 158,511.
- Symbols: 163.
- OHLCV hash: `9f539f38394240f5dcd922b23d234008a84a357c38ef9f2d8197acfab80d7e14`.
- Instrument hash: `df7777139dd4106032280339818ba18179882c8e19141f374d87cb8e7bddf18b`.

## Validation Checks

`make validate-data` checks:

- required columns and dtypes;
- unique `(bar_start_utc, symbol)` keys;
- UTC timestamp semantics;
- OHLC sanity;
- manifest hashes;
- symbol coverage;
- full-mode universe eligibility proof.

The current data-validation proof reports 104 eligible and scored pairs at
`2025-07-01T00:00:00+00:00`. The final-test Level 5 proof reports 120 eligible
and scored pairs.

## Artifact Layout

Per-level artifacts:

| Directory | Content |
| --- | --- |
| `artifacts/metrics/` | CSV metrics and metadata |
| `artifacts/equity/` | NAV/equity curves |
| `artifacts/weights/` | target/actual weights |
| `artifacts/orders/` | order intents and rejections |
| `artifacts/fills/` | simulated fills |
| `artifacts/figures/` | equity and summary figures |
| `artifacts/monitoring/` | traces, alerts, proofs, health summaries |

Final-test artifacts:

```text
artifacts/final_test_lock.json
artifacts/final_test_lock.json.metadata.json
artifacts/final_test/c33b5eb396f6/
```

Accepted final-test lock:

```text
c33b5eb396f60b1e2a7890616b8d9ae1cd69e91375dec925b68b6673d843af5e
```

## Provenance Contract

Every material output identifies or links to:

- data hash;
- instrument hash;
- config hash;
- git commit;
- final-test lock hash;
- period and split;
- benchmark;
- cost assumptions;
- seed where applicable;
- validation or final-test status.

`make verify-final-lock` validates the frozen contract and fails closed on hash
mismatches.

## Release-Facing Reports

The public report set is intentionally small:

```text
reports/final_report.md
reports/data_card.md
reports/model_cards/
```

Internal stage logs and development audit scratchpads are not required for the
final submission and are not tracked in the cleaned public tree.
