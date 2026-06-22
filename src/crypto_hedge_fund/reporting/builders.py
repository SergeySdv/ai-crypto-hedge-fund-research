"""Build Stage 12 notebook, report and presentation from committed artifacts."""

from __future__ import annotations

import base64
import json
import re
import subprocess
import sys
import tempfile
import textwrap
from collections.abc import Iterable
from hashlib import sha1
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import nbformat
from matplotlib.backends.backend_pdf import PdfPages

from crypto_hedge_fund.reporting.context import (
    LEVELS,
    Stage12Context,
    format_float,
    format_usd,
    load_stage12_context,
    markdown_table,
    selected_rows_for_markdown,
)


def build_final_report(repo_root: Path | str = Path(".")) -> Path:
    """Write the reviewer-facing final report from committed final-test artifacts."""

    context = load_stage12_context(repo_root)
    root = context.repo_root
    report_path = root / "reports/final_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    counts = context.level5_counts
    costs = context.cost_assumptions
    runner_dirty = context.traces["level_5"]["provenance"]["git_worktree_dirty"]
    selected_rows = selected_rows_for_markdown(context)
    selected_table = markdown_table(
        selected_rows,
        [
            "Level",
            "Selected result",
            "Net return",
            "Net Sharpe",
            "Max drawdown",
            "Total costs",
            "Benchmark",
        ],
    )
    artifact_rows = _artifact_hash_rows(context)
    period_start, period_end = context.final_period
    final_dir = context.final_dir.relative_to(root).as_posix()

    report = f"""# Final Report - AI Crypto Hedge Fund Research MVP

## Scope and framing

This repository is an educational historical research system for an AI-agent crypto
portfolio workflow. It is not a profitability claim, not investment advice and not an
enabled live trading bot. The MVP is long-only, unlevered, spot-only, daily-bar and
USDT-cash based.

## Final-test lock and exposure

- Final-test exposure: `{context.suite_summary["final_test_exposure"]}`
- Accepted lock SHA-256: `{context.lock_hash}`
- Lock path: `artifacts/final_test_lock.json`
- Final-test artifact directory: `{final_dir}/`
- Final period: `{period_start}` through `{period_end}`
- Locked git commit: `{context.suite_summary["locked_git_commit"]}`
- Runner git commit: `{context.suite_summary["git_commit"]}`
- Runner source dirty during frozen final suite: `{runner_dirty}`
- Data hash: `{context.suite_summary["data_sha256"]}`
- Validation-selected config hash: `{context.suite_summary["validation_selected_sha256"]}`
- Generated final config hash: `{context.suite_summary["generated_final_config_sha256"]}`

The final-test suite is already exposed. The report builder does not rerun final-test
experiments or alter methodology; it reads the committed frozen artifacts.

## Data, execution and costs

- Timestamp convention: daily bars are UTC bar-start records; completed-bar features
  execute at the next available open.
- Cost convention: fee-bearing notional is risky-asset notional actually traded.
- One-way fee: `{costs["fee_bps_one_way"]}` bps.
- One-way slippage: `{costs["slippage_bps_one_way"]}` bps.
- Initial capital: `{format_usd(costs["initial_capital_usd"])}`.
- Risk-free rate: `{costs["risk_free_rate"]}`.

## Final-test selected results

{selected_table}

Net after fees and slippage is primary. Several selected strategies underperformed
their benchmark in the exposed final year; those are research findings, not failures
to be hidden. The final-test evidence does not establish robust alpha.

## Level 5 proof

- Eligible pairs: `{counts["eligible_count"]}`
- Scored pairs: `{counts["scored_count"]}`
- Selected holdings: `{counts["selected_count"]}`
- Runtime: `{format_float(counts["runtime_seconds"], 1)}` seconds.
- Peak RSS: `{format_float(counts["peak_rss_mb"], 1)}` MiB.
- Proof artifact: `{final_dir}/monitoring/level_5_pair_count_proof.json`

## Agent interaction trace

The notebook displays a readable Level 2 trace from agent outputs to aggregate signal,
portfolio proposal and risk approval. The committed trace shows SMA, econometric,
logistic-regression and gradient-boosting agents emitting typed scores/confidence with
cutoffs and reason codes. The aggregate signal was negative for BTC/USDT on the shown
decision, so the approved portfolio was cash with reason code `ok`.

## Monitoring and fail-safes

The final Level 5 health summary reports system status
`{context.health_summary.iloc[0]["system_status"]}`, eligible/scored count ranges
`{context.health_summary.iloc[0]["eligible_count_min"]}`-`{context.health_summary.iloc[0]["eligible_count_max"]}`,
and `{context.health_summary.iloc[0]["incident_count"]}` monitoring incidents.
Demonstrated fail-safe scenarios include
`{context.health_summary.iloc[0]["fail_safe_scenarios_demonstrated"]}`.

## Artifact hashes

{markdown_table(artifact_rows, ["Artifact", "SHA-256"])}

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
"""
    report_path.write_text(report, encoding="utf-8")
    return report_path


def build_notebook(
    repo_root: Path | str = Path("."),
    *,
    smoke: bool = False,
    execute: bool = True,
) -> Path:
    """Create the single final notebook and optionally execute it in a fresh process."""

    context = load_stage12_context(repo_root)
    root = context.repo_root
    notebook_path = root / "notebooks/ai_crypto_hedge_fund.ipynb"
    notebook_path.parent.mkdir(parents=True, exist_ok=True)
    nb = nbformat.v4.new_notebook()
    nb.metadata = {
        "kernelspec": {
            "display_name": "Python 3.11 (.venv: crypto-hedge-fund)",
            "language": "python",
            "name": "python3",
        },
        "language_info": {
            "name": "python",
            "pygments_lexer": "ipython3",
            "version": "3.11",
        },
        "stage12_execution": {
            "executor": "fresh-python-subprocess",
            "smoke": smoke,
            "final_test_lock_sha256": context.lock_hash,
        },
    }
    nb.cells = _notebook_cells(smoke=smoke)
    _assign_stable_cell_ids(nb.cells)
    _hide_code_cell_sources(nb.cells)
    if execute:
        _execute_notebook_cells(nb, cwd=root)
    nbformat.write(nb, notebook_path)
    _format_notebook_file(notebook_path, cwd=root)
    _sanitize_notebook_file(notebook_path)
    return notebook_path


def build_presentation(repo_root: Path | str = Path(".")) -> tuple[Path, Path, int]:
    """Write Marp-compatible source, render a PDF and verify page count."""

    context = load_stage12_context(repo_root)
    root = context.repo_root
    presentation_dir = root / "presentation"
    presentation_dir.mkdir(parents=True, exist_ok=True)
    deck_path = presentation_dir / "deck.md"
    pdf_path = presentation_dir / "deck.pdf"
    deck_path.write_text(_deck_markdown(context), encoding="utf-8")
    _render_deck_pdf(deck_path=deck_path, pdf_path=pdf_path)
    page_count = count_pdf_pages(pdf_path)
    if page_count > 10:
        raise RuntimeError(f"presentation/deck.pdf has {page_count} pages; maximum is 10")
    return deck_path, pdf_path, page_count


def count_pdf_pages(path: Path | str) -> int:
    """Count PDF pages without adding a PDF dependency."""

    payload = Path(path).read_bytes()
    return len(re.findall(rb"/Type\s*/Page\b", payload))


def _artifact_hash_rows(context: Stage12Context) -> list[dict[str, object]]:
    final_dir = context.final_dir.relative_to(context.repo_root)
    paths = [
        Path("artifacts/final_test_lock.json"),
        final_dir / "final_test_suite_summary.json",
        final_dir / "monitoring/level_5_pair_count_proof.json",
        final_dir / "monitoring/health_summary.csv",
    ]
    for level in LEVELS:
        paths.append(final_dir / f"metrics/{level}.csv")
    rows = []
    from crypto_hedge_fund.provenance import file_sha256

    for relative in paths:
        rows.append(
            {"Artifact": str(relative), "SHA-256": file_sha256(context.repo_root / relative)}
        )
    return rows


def _assign_stable_cell_ids(cells: list[Any]) -> None:
    for index, cell in enumerate(cells):
        payload = f"{cell.cell_type}\n{cell.source}".encode()
        cell["id"] = f"cell-{index:02d}-{sha1(payload).hexdigest()[:12]}"


def _hide_code_cell_sources(cells: list[Any]) -> None:
    for cell in cells:
        if cell.cell_type == "code":
            cell.metadata.setdefault("jupyter", {})["source_hidden"] = True


def _notebook_cells(*, smoke: bool) -> list[Any]:
    mode = "FAST SMOKE - NON-FINAL CHECK" if smoke else "FULL FINAL NOTEBOOK"
    return [
        nbformat.v4.new_markdown_cell(
            f"""# AI Crypto Hedge Fund - Final Notebook

Execution mode: **{mode}**.

This notebook is the single end-to-end reviewer narrative. It imports repository
package code and reads committed validation/final-test artifacts. It does not place
orders, download live data, call an external LLM or rerun/tune final-test strategies.
"""
        ),
        nbformat.v4.new_code_cell(
            f"""import os
import sys
from pathlib import Path


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "pyproject.toml").exists() and (candidate / "src").exists():
            return candidate
    raise RuntimeError("Cannot locate repository root from notebook working directory.")


ROOT = find_repo_root(Path.cwd().resolve())
EXPECTED_VENV = (ROOT / ".venv").resolve()
RUNNING_PYTHON = Path(sys.executable).resolve()
RUNNING_PREFIX = Path(sys.prefix).resolve()
if RUNNING_PREFIX != EXPECTED_VENV:
    raise RuntimeError(
        "This notebook must run with the repository uv environment. "
        f"Run `uv sync --frozen`, then select {{EXPECTED_VENV / 'bin/python'}} "
        f"or run `make notebook-full`. Current interpreter: {{RUNNING_PYTHON}}; "
        f"current sys.prefix: {{RUNNING_PREFIX}}"
    )
os.chdir(ROOT)

import pandas as pd
from IPython.display import display

from crypto_hedge_fund.reporting import load_stage12_context
from crypto_hedge_fund.reporting.context import (
    representative_trace_rows,
)
from crypto_hedge_fund.reporting.notebook_display import (
    compact_frame,
    configure_notebook_display,
    format_cell,
    key_value_frame,
    plot_return_overview,
    plot_selected_nav,
    selected_summary_frame,
    short_hash,
)

configure_notebook_display()
ctx = load_stage12_context(ROOT)
print("final_test_lock_sha256:", ctx.lock_hash)
print("final_test_exposure:", ctx.suite_summary["final_test_exposure"])
print("final_test_dir:", ctx.final_dir.relative_to(ROOT).as_posix())
print("stage12_mode:", "{mode}")
"""
        ),
        nbformat.v4.new_markdown_cell(
            """## 1. Executive summary and coherent fund vision

The system is a reproducible historical research MVP for a risk-first AI-assisted
crypto portfolio. Agents produce scored proposals with confidence and cutoffs;
deterministic risk, allocation, rebalance and execution layers decide what can be
simulated. The MVP is long-only, unlevered, daily spot and educational.
"""
        ),
        nbformat.v4.new_code_cell("""display(selected_summary_frame(ctx))"""),
        nbformat.v4.new_markdown_cell(
            """## 2. Reproducibility/environment/data hashes

The final-test lock and artifact metadata identify data, config, git, costs, period,
benchmark and seed values. The accepted lock is shown by package code above.
"""
        ),
        nbformat.v4.new_code_cell(
            """summary = ctx.suite_summary
display(key_value_frame([
    ("Data SHA-256", short_hash(summary["data_sha256"])),
    ("Instruments SHA-256", short_hash(summary["instruments_sha256"])),
    ("Manifest SHA-256", short_hash(summary["manifest_sha256"])),
    ("Validation config SHA-256", short_hash(summary["validation_selected_sha256"])),
    ("Generated final config SHA-256", short_hash(summary["generated_final_config_sha256"])),
    ("Locked git commit", short_hash(summary["locked_git_commit"])),
    ("Runner git commit", short_hash(summary["git_commit"])),
    ("Period", summary["period"]),
    ("Costs", summary["cost_assumptions"]),
]))"""
        ),
        nbformat.v4.new_markdown_cell(
            """## 3. Data preparation, provenance and quality

The included dataset is frozen daily spot OHLCV with instrument metadata and a manifest.
It is validated offline and carries the known active-market survivorship/delisting
limitation.
"""
        ),
        nbformat.v4.new_code_cell(
            """counts = ctx.level5_counts
health = ctx.health_summary.iloc[0]
display(key_value_frame([
    ("Level 5 eligible pairs", counts["eligible_count"]),
    ("Level 5 scored pairs", counts["scored_count"]),
    ("Level 5 selected holdings", counts["selected_count"]),
    ("System status", health["system_status"]),
    ("Incident count", health["incident_count"]),
    ("Fail-safe scenarios", health["fail_safe_scenarios_demonstrated"]),
    ("Runtime", format_cell(counts["runtime_seconds"], "runtime_seconds")),
    ("Peak RSS", format_cell(counts["peak_rss_mb"], "peak_rss_mb")),
]))"""
        ),
        nbformat.v4.new_markdown_cell(
            """## 4. Architecture and agent interaction trace

The shared flow is: frozen data -> causal features -> typed agents -> aggregator ->
pre-risk -> allocator -> rebalance controller -> post-risk -> orders/fills -> ledger
-> metrics/monitoring. The next cell prints a committed end-to-end Level 2 trace.
"""
        ),
        nbformat.v4.new_code_cell(
            """trace_rows = representative_trace_rows(ctx)
trace = pd.DataFrame(trace_rows)
display(compact_frame(
    trace,
    ["agent", "symbol", "score", "confidence", "fit_cutoff", "feature_cutoff", "reason_codes"],
    max_rows=10,
))"""
        ),
        nbformat.v4.new_markdown_cell(
            """## 5. Model validation and no-leakage protocol

Train data covers 2021-2023, validation covers 2024, and the frozen final test covers
2025. Stage 12 consumes the exposed final artifacts and does not retune choices.
"""
        ),
        *_level_notebook_cells(),
        nbformat.v4.new_markdown_cell(
            """## 11. Cross-level comparison, monitoring and fail-safes

Net after fees/slippage is primary. Monitoring includes data/model/system health,
agent disagreement, optimizer fallback, runtime, incidents and explicit fail-safe
scenarios.
"""
        ),
        nbformat.v4.new_code_cell(
            """display(selected_summary_frame(ctx))
display(key_value_frame([
    ("Level 5 eligible pairs", ctx.level5_pair_count_proof["eligible_count"]),
    ("Level 5 scored pairs", ctx.level5_pair_count_proof["scored_count"]),
    ("Level 5 selected holdings", ctx.level5_pair_count_proof["selected_count"]),
    ("Approved nonzero max", ctx.level5_pair_count_proof["approved_nonzero_count_max"]),
]))
plot_return_overview(ctx)
plot_selected_nav(ctx)"""
        ),
        nbformat.v4.new_markdown_cell(
            """## 12. Limitations, real-trading application and production roadmap

Limitations: active-market survivorship/delisting bias, daily-bar liquidity proxies,
USDT cash assumption, simplified fills, cash-heavy risk behavior, and Level 5 top-K
benchmark rather than a full eligible-universe basket. Future work includes
multi-CEX adapters, order-book liquidity, reconciliation, Telegram controls and
news/sentiment ingestion. Those future items are not enabled in this MVP.
"""
        ),
    ]


def _level_notebook_cells() -> list[Any]:
    headings = {
        "level_1": "## 6. Level 1 \u2014 Baseline Strategy for a Single Cryptocurrency.",
        "level_2": "## 7. Level 2 \u2014 Adding AI Agents, Econometrics and ML.",
        "level_3": (
            "## 8. Level 3 \u2014 Portfolio Management on Historical Data "
            "(5\u20137 assets, prior 12 months)."
        ),
        "level_4": "## 9. Level 4 \u2014 Dynamic Portfolio Rebalancing.",
        "level_5": "## 10. Level 5 \u2014 Portfolio Expansion to 100+ Pairs.",
    }
    descriptions = {
        "level_1": "BTC/USDT SMA baseline through the shared next-open engine.",
        "level_2": "Single-pair technical, econometric, ML and ensemble agents.",
        "level_3": "Static 5-7 asset portfolio estimated from the prior 12 months.",
        "level_4": "Dynamic small-portfolio rebalance policies selected on validation.",
        "level_5": "Large-universe point-in-time scoring with dynamic top-K allocation.",
    }
    cells: list[Any] = []
    for level in LEVELS:
        cells.append(nbformat.v4.new_markdown_cell(f"{headings[level]}\n\n{descriptions[level]}"))
        cells.append(
            nbformat.v4.new_code_cell(
                f"""frame = ctx.metrics["{level}"]
important = [
    "approach", "method", "policy", "selected_for_{level}",
    "net_total_return", "net_sharpe", "net_max_drawdown",
    "net_turnover", "net_total_cost", "net_benchmark_total_return",
    "eligible_count", "scored_count", "selected_count",
    "runtime_seconds", "peak_rss_mb",
]
display(compact_frame(frame, important, max_rows=8))"""
            )
        )
    return cells


def _execute_notebook_cells(nb: Any, *, cwd: Path) -> None:
    code_cells = [
        (index, cell.source) for index, cell in enumerate(nb.cells) if cell.cell_type == "code"
    ]
    script = _execution_script([source for _, source in code_cells])
    with tempfile.TemporaryDirectory() as temp_dir:
        script_path = Path(temp_dir) / "execute_notebook.py"
        script_path.write_text(script, encoding="utf-8")
        result = subprocess.run(
            [str(_project_python(cwd)), str(script_path)],
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )
    if result.returncode != 0:
        raise RuntimeError(
            f"notebook execution failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    outputs = _parse_cell_outputs(result.stdout)
    for output_index, (cell_index, _) in enumerate(code_cells):
        cell = nb.cells[cell_index]
        cell.execution_count = output_index + 1
        output_payload = outputs.get(output_index, {"text": "", "display_data": []})
        cell.outputs = []
        if output_payload["text"]:
            cell.outputs.append(
                nbformat.v4.new_output(
                    "stream",
                    name="stdout",
                    text=output_payload["text"],
                )
            )
        for display_data in output_payload["display_data"]:
            cell.outputs.append(
                nbformat.v4.new_output(
                    "display_data",
                    data=display_data,
                    metadata={},
                )
            )


def _format_notebook_file(notebook_path: Path, *, cwd: Path) -> None:
    result = subprocess.run(
        ["ruff", "format", str(notebook_path.relative_to(cwd))],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"notebook formatting failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )


def _sanitize_notebook_file(notebook_path: Path) -> None:
    """Remove non-standard frontend keys before nbconvert validation."""

    payload = json.loads(notebook_path.read_text(encoding="utf-8"))
    allowed_by_type = {
        "stream": {"output_type", "name", "text"},
        "display_data": {"output_type", "data", "metadata", "transient"},
        "execute_result": {"output_type", "data", "metadata", "execution_count"},
        "error": {"output_type", "ename", "evalue", "traceback"},
    }
    for cell in payload.get("cells", []):
        if "outputs" not in cell:
            continue
        clean_outputs = []
        for output in cell["outputs"]:
            allowed = allowed_by_type.get(output.get("output_type"))
            clean_outputs.append(
                output
                if allowed is None
                else {key: value for key, value in output.items() if key in allowed}
            )
        cell["outputs"] = clean_outputs
    nbformat.validate(nbformat.from_dict(payload))
    notebook_path.write_text(
        json.dumps(payload, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def _project_python(root: Path) -> Path:
    for relative in (".venv/bin/python3", ".venv/bin/python"):
        candidate = root / relative
        if candidate.exists():
            return candidate
    return Path(sys.executable)


def _execution_script(code_cells: list[str]) -> str:
    encoded = json.dumps(code_cells)
    return f"""import base64
import contextlib
import io
import json
import traceback

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from IPython import display as ipython_display

cells = json.loads({encoded!r})
namespace = {{}}


def _display_payload(obj):
    if hasattr(obj, "_repr_html_"):
        html = obj._repr_html_()
        if html:
            return {{"text/html": html, "text/plain": repr(obj)}}
    return {{"text/plain": repr(obj)}}


def _capture_figures(display_data):
    for figure_number in plt.get_fignums():
        figure = plt.figure(figure_number)
        buffer = io.BytesIO()
        figure.savefig(buffer, format="png", bbox_inches="tight", dpi=130)
        display_data.append(
            {{"image/png": base64.b64encode(buffer.getvalue()).decode("ascii")}}
        )
    plt.close("all")


for index, source in enumerate(cells):
    display_data = []

    def _display(*objects, **_kwargs):
        for obj in objects:
            display_data.append(_display_payload(obj))

    ipython_display.display = _display
    namespace["display"] = _display
    stdout_buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout_buffer):
            exec(compile(source, f"<notebook-cell-{{index}}>", "exec"), namespace)
        _capture_figures(display_data)
    except Exception:
        print(stdout_buffer.getvalue(), end="")
        traceback.print_exc()
        raise
    payload = {{"text": stdout_buffer.getvalue(), "display_data": display_data}}
    encoded_payload = base64.b64encode(json.dumps(payload).encode("utf-8")).decode("ascii")
    print(f"@@CELL_OUTPUT {{index}} {{encoded_payload}}@@")
"""


def _parse_cell_outputs(stdout: str) -> dict[int, dict[str, Any]]:
    outputs: dict[int, dict[str, Any]] = {}
    pattern = re.compile(r"@@CELL_OUTPUT (\d+) ([A-Za-z0-9+/=]+)@@")
    for match in pattern.finditer(stdout):
        payload_bytes = base64.b64decode(match.group(2).encode("ascii"), validate=True)
        outputs[int(match.group(1))] = json.loads(payload_bytes.decode("utf-8"))
    return outputs


def _deck_markdown(context: Stage12Context) -> str:
    rows = selected_rows_for_markdown(context)
    compact_rows = [
        {
            "Level": row["Level"],
            "Selected": row["Selected result"],
            "Net return": row["Net return"],
            "Sharpe": row["Net Sharpe"],
            "MDD": row["Max drawdown"],
        }
        for row in rows
    ]
    counts = context.level5_counts
    level5_count_text = (
        f"{counts['eligible_count']} eligible, "
        f"{counts['scored_count']} scored, "
        f"{counts['selected_count']} selected"
    )
    runtime_text = (
        f"{format_float(counts['runtime_seconds'], 1)}s; "
        f"peak RSS: {format_float(counts['peak_rss_mb'], 1)} MiB"
    )
    return f"""---
marp: true
title: AI Crypto Hedge Fund Research MVP
paginate: true
---

# Hedge Fund Model
## Mandate and investment universe

- Educational, historical AI-assisted crypto research MVP.
- Long-only, unlevered daily spot USDT universe; cash is explicit.
- Strategy sleeves: technical, econometric, ML and cross-sectional scoring.
- Future: multi-CEX automation, but no live order submission is enabled.

---

# Hedge Fund Model
## AI/ML and agent interaction

- Classical indicators are transparent baseline signals.
- Logistic regression, gradient boosting, AutoReg/GARCH and deterministic
  cross-sectional scoring agents are used.
- Agents emit score, confidence, horizon, cutoffs and reason codes.
- Aggregation proposes exposure; deterministic risk can veto or move to cash.

---

# Risk Management
## Taxonomy and metrics

- Market, drawdown/tail, concentration/correlation and liquidity/capacity risk.
- Model, data and operational failures are tracked separately from returns.
- Metrics include volatility, VaR/CVaR, drawdown, exposure, turnover and costs.
- Level 5 health status: `{context.health_summary.iloc[0]["system_status"]}`.

---

# Risk Management
## AI support and deterministic controls

- GARCH/realized volatility and regime state inform risk budgets.
- Pre-allocation risk blocks stale, illiquid or invalid inputs.
- Post-allocation risk validates weights, turnover, concentration and cash.
- Fail-safes include volatility cash approval, invalid feature alerts and reconciliation checks.

---

# Portfolio Management
## Theory and "optimal" portfolio

- MPT and minimum variance give transparent objectives but face estimation error.
- Equal weight and inverse volatility remain robust baselines.
- CVaR/downside methods address tail risk directly.
- Submitted methods were selected on validation, not on final-test returns.

---

# Portfolio Management
## Static, dynamic and large universe

- Level 3: 5-7 assets, exactly prior 12-month estimation, static OOS hold.
- Level 4: calendar/drift/signal/risk rebalance policy.
- Level 5: point-in-time 100+ universe, top-K 25, capacity and turnover controls.
- Target weights become next-open simulated orders through one shared broker.

---

# System Architecture
## End-to-end block diagram

```text
Frozen OHLCV -> quality gate -> causal features -> signal agents
  -> orchestrator -> pre-risk -> allocator -> rebalance controller
  -> post-risk -> order generator -> simulated broker -> ledger
  -> metrics, monitoring, notebook and deck
```

Future CEX adapters are disabled; simulator artifacts are the submitted evidence.

---

# System Architecture
## Interactions, monitoring and roadmap

1. Completed daily bar creates features.
2. Agents emit typed proposals with cutoffs and confidence.
3. Risk and portfolio layers approve, cap or reject.
4. Orders fill at next open; ledger writes gross/net metrics.
5. Monitoring records freshness, drift, disagreement, incidents and runtime.

---

# Technical Evidence
## Frozen protocol and Level 5 count

- Train: 2021-2023; validation: 2024; final test: 2025.
- Accepted final lock: `{context.lock_hash}`.
- Final-test exposure: `{context.suite_summary["final_test_exposure"]}`.
- Level 5 final count: {level5_count_text}.
- Runtime: {runtime_text}.

---

# Results and Limitations
## Net final-test evidence

{markdown_table(compact_rows, ["Level", "Selected", "Net return", "Sharpe", "MDD"])}

Limitations: active-market survivorship/delisting bias, daily-bar liquidity proxy,
short late-December 2024 Level 5 validation proof window, cash-heavy risk behavior,
and Level 5 top-K benchmark rather than a full eligible-universe basket. Results did
not establish robust alpha.
"""


def _render_deck_pdf(*, deck_path: Path, pdf_path: Path) -> None:
    slides = _split_slides(deck_path.read_text(encoding="utf-8"))
    with PdfPages(pdf_path) as pdf:
        for slide_number, slide in enumerate(slides, start=1):
            fig = plt.figure(figsize=(13.33, 7.5), facecolor="white")
            ax = fig.add_axes((0, 0, 1, 1))
            ax.axis("off")
            _draw_slide(ax, slide=slide, slide_number=slide_number, slide_count=len(slides))
            pdf.savefig(fig)
            plt.close(fig)


def _split_slides(markdown: str) -> list[str]:
    body = re.sub(r"\A---\n.*?\n---\n", "", markdown, count=1, flags=re.DOTALL)
    slides = [slide.strip() for slide in re.split(r"\n---\n", body) if slide.strip()]
    if not slides:
        raise RuntimeError("deck source contains no slides")
    return slides


def _draw_slide(ax: Any, *, slide: str, slide_number: int, slide_count: int) -> None:
    title, subtitle, body_lines = _parse_slide(slide)
    ax.text(
        0.06,
        0.88,
        title,
        fontsize=25,
        fontweight="bold",
        color="#1f2937",
        va="top",
    )
    if subtitle:
        ax.text(0.06, 0.80, subtitle, fontsize=16, color="#2563eb", va="top")
    y = 0.70
    for line in body_lines:
        if not line:
            y -= 0.035
            continue
        wrapped = textwrap.wrap(line, width=95) or [line]
        prefix = "\u2022 " if line.startswith("- ") else ""
        first = wrapped[0][2:] if line.startswith("- ") else wrapped[0]
        ax.text(0.08, y, prefix + first, fontsize=11.5, color="#111827", va="top")
        y -= 0.045
        for continuation in wrapped[1:]:
            ax.text(0.105, y, continuation, fontsize=11.5, color="#111827", va="top")
            y -= 0.040
        if y < 0.12:
            ax.text(0.08, y, "...", fontsize=11.5, color="#111827", va="top")
            break
    ax.text(
        0.94,
        0.04,
        f"{slide_number}/{slide_count}",
        fontsize=9,
        color="#6b7280",
        ha="right",
    )


def _parse_slide(slide: str) -> tuple[str, str, list[str]]:
    lines = [line.rstrip() for line in slide.splitlines()]
    title = "AI Crypto Hedge Fund"
    subtitle = ""
    body: list[str] = []
    in_fence = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if stripped.startswith("# "):
            title = stripped[2:].strip()
        elif stripped.startswith("## "):
            subtitle = stripped[3:].strip()
        elif stripped.startswith("<!--"):
            continue
        elif stripped and not stripped.startswith("---"):
            if in_fence:
                body.append(stripped)
            else:
                body.append(stripped.replace("`", ""))
    return title, subtitle, _trim_table_lines(body)


def _trim_table_lines(lines: Iterable[str]) -> list[str]:
    trimmed: list[str] = []
    for line in lines:
        if line.startswith("| ---"):
            continue
        if line.startswith("| "):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            trimmed.append(" | ".join(cells))
        else:
            trimmed.append(line)
    return trimmed
