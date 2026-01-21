from __future__ import annotations

from dataclasses import dataclass


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def norm_cosine(score: float) -> float:
    return clamp(score, 0.0, 1.0)


@dataclass(frozen=True)
class ConfidenceResult:
    confidence: float
    top_score: float
    mean_top3: float


def compute_confidence(scores: list[float], coverage: float = 0.0) -> ConfidenceResult:
    if not scores:
        return ConfidenceResult(confidence=0.0, top_score=0.0, mean_top3=0.0)

    s1 = scores[0]
    top3 = scores[:3]
    mean_top3 = sum(top3) / len(top3)

    c = (
        0.55 * norm_cosine(s1)
        + 0.35 * norm_cosine(mean_top3)
        + 0.10 * clamp(coverage)
    )
    return ConfidenceResult(confidence=clamp(c), top_score=s1, mean_top3=mean_top3)