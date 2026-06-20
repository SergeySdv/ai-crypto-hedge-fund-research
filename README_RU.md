# Audited handoff-пакет для Codex: AI Crypto Hedge Fund

Это версия после повторной проверки всех 7 страниц исходного задания. Она специально исправляет архитектурные риски, которые возникают, если реализовывать уровни по очереди без общего плана.

Главные файлы:

1. [`AGENTS.md`](AGENTS.md) — обязательный контракт для coding-агента.
2. [`CODEX_PROMPT.md`](CODEX_PROMPT.md) — готовый стартовый prompt.
3. [`docs/00_GLOBAL_PLAN_AND_AUDIT.md`](docs/00_GLOBAL_PLAN_AND_AUDIT.md) — общий план всех уровней и найденные неочевидные зависимости.
4. [`docs/11_REQUIREMENTS_TRACEABILITY.md`](docs/11_REQUIREMENTS_TRACEABILITY.md) — построчная матрица требований исходного задания.
5. [`docs/12_FINAL_TEST_FREEZE_AND_SUBMISSION.md`](docs/12_FINAL_TEST_FREEZE_AND_SUBMISSION.md) — защита final test от подглядывания и чек-лист сдачи.

## Что было уточнено после аудита

- Архитектура обязана быть multi-asset/panel-native с первого уровня.
- Нельзя смотреть final-test результаты каждого уровня по мере разработки; все пять уровней сначала замораживаются, затем тестируются вместе.
- Сделка по сигналу закрытой свечи должна исполняться на следующем open, а не на том же close.
- Risk layer должен работать до и после portfolio allocation.
- Level 3 использует ровно предыдущие 12 месяцев для расчёта статических весов.
- Level 5 считается выполненным только после фактической обработки минимум 100 пар.
- Frozen dataset должен физически поставляться с проектом и позволять offline-запуск notebook.
- Нужны не только классы с названием Agent, но и реальное типизированное взаимодействие, abstain/failure handling и audit trace.
- Презентация должна быть экспортирована в `deck.pdf`, максимум 10 слайдов.
- Исправлена модель transaction costs для asset-to-asset rotation.
- Добавлены long-term quality metrics, fail-safe scenarios, clean-clone rehearsal и public-repository checklist.

## Ожидаемый результат

- публичный GitHub/GitLab проект;
- один выполненный notebook;
- modular `src/` package;
- frozen OHLCV для 100+ пар;
- out-of-sample результаты Levels 1–5;
- risk/performance metrics, статистическая проверка и benchmarks;
- typed agent orchestration;
- Docker/CI/tests;
- до 10 слайдов в PDF;
- traceability и final-test lock.

Передайте Codex весь каталог и попросите строго следовать `AGENTS.md`, а не только `CODEX_PROMPT.md`.
