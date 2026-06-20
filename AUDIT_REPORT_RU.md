# Повторный аудит исходного задания

## Итог

Скрытого приложения или дополнительного блока требований в 7-страничном PDF нет. Но в первой версии handoff были несколько мест, которые могли привести к неверной архитектуре или формальному недовыполнению задания.

## Существенные исправления

1. **Общий multi-asset core с самого начала.** Level 1 теперь явно является конфигурацией общего portfolio engine с одной парой, а не отдельным одноактивным backtester.
2. **Final test нельзя смотреть по уровням.** Все Levels 1–5 сначала реализуются и выбираются на train/validation, затем создаётся lock и только после этого запускается единый final suite.
3. **Execution timing.** Сигнал по завершённой дневной свече исполняется на следующем open; прежнее допущение same-close могло вызвать претензию по look-ahead/реализуемости.
4. **Transaction costs.** Комиссия считается по фактически торгуемому risky notional; полный переход A→B включает продажу и покупку.
5. **Level 3: last 12 months.** Явно зафиксировано использование 2024 года для оценки статических весов и 2025 года для OOS.
6. **Выбор 5–7 монет без hindsight.** Universe определяется по ликвидности/coverage на cutoff, а не по известным позднее победителям.
7. **Risk до и после allocation.** Один pre-risk этап не способен проверить volatility/concentration уже построенного портфеля.
8. **AI agents должны реально взаимодействовать.** Добавлены orchestrator, typed messages, confidence, abstain/failure и end-to-end decision trace.
9. **AI-driven rebalancing в Level 5.** Изменение score/regime участвует в решении о ребалансировке, но deterministic risk сохраняет veto.
10. **100+ пар — жёсткий gate.** Недостаток данных нельзя закрыть только limitation note.
11. **Все данные физически поставляются.** Default notebook должен работать offline после checkout.
12. **Презентация как PDF.** Недостаточно одного `deck.md`; нужен `deck.pdf`, максимум 10 слайдов.
13. **Два слайда на каждый conceptual section.** Outline перестроен ближе к рекомендации задания.
14. **Long-term system quality.** Добавлены drift, calibration, agent disagreement, failure rates, runtime, artifact freshness и rolling stability.
15. **Реальное применение Level 3.** Добавлены weights→orders, precision/min-notional, liquidity, custody и reconciliation limitations.
16. **Order execution module.** В архитектуре теперь явно есть order generator, simulated broker, fills и future CEX port.
17. **Clean-clone и public repo proof.** Добавлен submission checklist и ручной шаг подтверждения публичного URL.

## Главный принцип для Codex

Не выполнять задание как цепочку из пяти независимых проектов. Сначала зафиксировать общие данные, clock, execution, cost, risk, portfolio и artifact contracts; затем включать возможности по уровням. Final-test период не открывать до полной заморозки всех пяти уровней.
