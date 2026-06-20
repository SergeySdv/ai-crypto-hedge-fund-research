"""Signal aggregation with abstentions, confidence weights and disagreement."""

from __future__ import annotations

from dataclasses import dataclass, field

from crypto_hedge_fund.types import AgentSignal, AggregatedSignal, ReasonCode


def _dedupe_reasons(codes: list[ReasonCode]) -> tuple[ReasonCode, ...]:
    seen: set[ReasonCode] = set()
    ordered: list[ReasonCode] = []
    for code in codes:
        if code not in seen:
            ordered.append(code)
            seen.add(code)
    return tuple(ordered) or (ReasonCode.OK,)


@dataclass(frozen=True)
class SignalAggregator:
    """Combine per-agent proposals into one typed signal per symbol."""

    agent_weights: dict[str, float] = field(default_factory=dict)
    min_confidence: float = 0.0
    disagreement_threshold: float = 0.75

    def aggregate(
        self, signals: list[AgentSignal], symbols: tuple[str, ...]
    ) -> list[AggregatedSignal]:
        by_symbol = {symbol: [] for symbol in symbols}
        for signal in signals:
            if signal.symbol in by_symbol:
                by_symbol[signal.symbol].append(signal)

        aggregated: list[AggregatedSignal] = []
        for symbol in symbols:
            symbol_signals = by_symbol[symbol]
            active = [
                signal
                for signal in symbol_signals
                if ReasonCode.ABSTAIN not in signal.reason_codes and signal.confidence > 0
            ]
            reasons: list[ReasonCode] = []
            for signal in symbol_signals:
                reasons.extend(signal.reason_codes)
            contributions: dict[str, float] = {}
            if not active:
                aggregated.append(
                    AggregatedSignal(
                        symbol=symbol,
                        score=0.0,
                        confidence=0.0,
                        contributions={signal.agent: 0.0 for signal in symbol_signals},
                        disagreement=0.0,
                        reason_codes=_dedupe_reasons([ReasonCode.ABSTAIN, *reasons]),
                    )
                )
                continue

            effective_weights = [
                max(0.0, self.agent_weights.get(signal.agent, 1.0)) * signal.confidence
                for signal in active
            ]
            total_effective_weight = sum(effective_weights)
            if total_effective_weight <= 0:
                aggregated.append(
                    AggregatedSignal(
                        symbol=symbol,
                        score=0.0,
                        confidence=0.0,
                        contributions={signal.agent: 0.0 for signal in symbol_signals},
                        disagreement=0.0,
                        reason_codes=_dedupe_reasons([ReasonCode.ABSTAIN, *reasons]),
                    )
                )
                continue

            score = 0.0
            for signal, effective_weight in zip(active, effective_weights, strict=True):
                contribution = signal.score * effective_weight / total_effective_weight
                contributions[signal.agent] = contribution
                score += contribution
            for signal in symbol_signals:
                contributions.setdefault(signal.agent, 0.0)
            scores = [signal.score for signal in active]
            disagreement = (max(scores) - min(scores)) / 2.0 if len(scores) > 1 else 0.0
            confidence = min(1.0, total_effective_weight / max(1, len(active)))
            if confidence < self.min_confidence:
                reasons.append(ReasonCode.ABSTAIN)
            if disagreement > self.disagreement_threshold:
                reasons.append(ReasonCode.AGENT_DISAGREEMENT)
            aggregated.append(
                AggregatedSignal(
                    symbol=symbol,
                    score=score,
                    confidence=confidence,
                    contributions=contributions,
                    disagreement=disagreement,
                    reason_codes=_dedupe_reasons(reasons or [ReasonCode.OK]),
                )
            )
        return aggregated
