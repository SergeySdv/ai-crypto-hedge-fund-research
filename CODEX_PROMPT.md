# Ready-to-paste prompt for Codex

Implement the complete AI Crypto Hedge Fund take-home project described by this handoff bundle.

Start with `AGENTS.md`. Then read every file in its “Read before editing” list. The most important context is in `docs/00_GLOBAL_PLAN_AND_AUDIT.md` and the exact source mapping is in `docs/11_REQUIREMENTS_TRACEABILITY.md`.

Do not begin by coding Level 1 in isolation. First design the shared panel-native architecture that must support all five levels. Level 1 and Level 2 are one-symbol configurations of the same multi-asset broker, ledger, risk and artifact system used by Levels 3–5.

Critical constraints:

- completed-bar features execute at the next available open;
- one shared cost/ledger implementation across all levels;
- pre-allocation and post-allocation risk gates;
- typed interacting agents plus an auditable decision trace;
- trailing 12-month estimation for Level 3;
- an actual full-mode run with at least 100 scored pairs for Level 5;
- frozen data physically included for an offline notebook run;
- no external LLM or private exchange key in the default path;
- one executed final notebook and one rendered PDF deck with at most 10 slides;
- no final-test inspection until all five levels and choices are frozen.

Workflow:

1. Inventory the current repository and report what can be preserved.
2. Freeze global architecture decisions and record any ambiguity in `docs/DECISIONS.md`.
3. Implement environment, data snapshot/manifest/validation and the shared panel-native kernel.
4. Implement Levels 1–5 on train/validation only.
5. Run tests and acceptance checks; create `artifacts/final_test_lock.json`.
6. Run the frozen final test suite for all levels.
7. Execute `notebooks/ai_crypto_hedge_fund.ipynb` in full mode and render `presentation/deck.pdf`.
8. Perform a clean-clone rehearsal.
9. Return a completion report with commands, artifacts, hashes, Level 5 symbol count, slide count, limitations and any manual publication step.

Do not fabricate results, silently downgrade requirements, copy from `denisalpino/autofin`, or optimize on final-test outcomes. Negative/inconclusive strategies are acceptable when the methodology is correct and explained.
