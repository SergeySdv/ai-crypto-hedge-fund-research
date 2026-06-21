# Stage 12 Deck Generator Fix Report

## Scope

Made the deck limitation fix reproducible by updating the presentation generator
`_deck_markdown` so future `make presentation` runs preserve the short
late-December 2024 Level 5 validation proof window limitation on the limitations
slide. No notebook, final report, configs, lock files, data, validation artifacts,
final-test artifacts or methodology were changed.

## Files changed

- `src/crypto_hedge_fund/reporting/builders.py`
- `presentation/deck.md`
- `presentation/deck.pdf`
- `tests/unit/test_stage12_reporting.py`
- `reports/agent_reports/stage_12_notebook_report_presentation/attempt_01/DECK_GENERATOR_FIX_REPORT.md`
- `reports/agent_reports/stage_12_notebook_report_presentation/attempt_01/command_logs/deck_generator_fix_make_presentation.log`
- `reports/agent_reports/stage_12_notebook_report_presentation/attempt_01/command_logs/deck_generator_fix_make_presentation.status`
- `reports/agent_reports/stage_12_notebook_report_presentation/attempt_01/command_logs/deck_generator_fix_make_presentation_rerun.log`
- `reports/agent_reports/stage_12_notebook_report_presentation/attempt_01/command_logs/deck_generator_fix_make_presentation_rerun.status`
- `reports/agent_reports/stage_12_notebook_report_presentation/attempt_01/command_logs/deck_generator_fix_stage12_reporting_test.log`
- `reports/agent_reports/stage_12_notebook_report_presentation/attempt_01/command_logs/deck_generator_fix_stage12_reporting_test.status`
- `reports/agent_reports/stage_12_notebook_report_presentation/attempt_01/command_logs/deck_generator_fix_pdf_page_count.log`
- `reports/agent_reports/stage_12_notebook_report_presentation/attempt_01/command_logs/deck_generator_fix_pdf_page_count.status`

## Commands and status

| Command | Status | Log |
| --- | ---: | --- |
| `make presentation` | 1 | `command_logs/deck_generator_fix_make_presentation.log` |
| `make presentation` rerun with corrected log wrapper | 0 | `command_logs/deck_generator_fix_make_presentation_rerun.log` |
| `uv run pytest tests/unit/test_stage12_reporting.py -q` | 0 | `command_logs/deck_generator_fix_stage12_reporting_test.log` |
| `mdls ... && file ... && uv run python ... pdf page count ...` | 0 | `command_logs/deck_generator_fix_pdf_page_count.log` |

The first `make presentation` invocation generated the deck successfully and reported
10 pages, but the shell wrapper failed afterward because `status` is a read-only zsh
variable. The rerun used `cmd_rc`, exited 0 and reported `pdf_page_count=10` and
`independent_pdf_page_count=10`.

The independent PDF page-count check reports:

- `kMDItemNumberOfPages = 10`
- `PDF document, version 1.4, 10 pages`
- `pdf_page_count_regex=10`

## Recommendation

Accept this narrow generator fix. Future `make presentation` runs now preserve the
short late-December 2024 Level 5 validation proof window limitation, and the focused
Stage 12 reporting test guards against regression.
