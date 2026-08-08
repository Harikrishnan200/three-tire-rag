"""Deterministic conflict resolution across evidence tiers.

Rules (in order):
1. Higher priority wins (tier1=100 > tier2=50 > tier3=10).
2. Tie on priority -> higher confidence wins.
3. Tie on confidence -> newer valid info wins (valid_from, then created_at).
4. Facts with non-overlapping/differing temporal validity are NOT merged —
   both are preserved with their temporal context attached.
Never silently merges contradictory facts; every resolution is recorded.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConflictRecord:
    subject: str
    predicate: str
    winner: dict[str, Any]
    losers: list[dict[str, Any]]
    reason: str


@dataclass
class ResolvedEvidence:
    facts: list[dict[str, Any]]
    conflicts: list[ConflictRecord] = field(default_factory=list)


class ConflictResolver:
    def resolve(self, evidence: list[dict[str, Any]]) -> ResolvedEvidence:
        groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for item in evidence:
            key = (str(item.get("subject", "")).strip().lower(), str(item.get("predicate", "")).strip().lower())
            groups.setdefault(key, []).append(item)

        resolved: list[dict[str, Any]] = []
        conflicts: list[ConflictRecord] = []

        for (subject, predicate), items in groups.items():
            if len(items) == 1:
                resolved.append(items[0])
                continue

            distinct_objects = {str(i.get("object", "")).strip().lower() for i in items}
            if len(distinct_objects) == 1:
                # Same fact from multiple sources - keep the highest-priority representation.
                best = self._pick_best(items)
                resolved.append(best)
                continue

            # Genuine contradiction: facts disagree on the object.
            # Preserve items with distinct, non-overlapping temporal validity separately.
            temporal_distinct = self._has_distinct_temporal_windows(items)
            if temporal_distinct:
                resolved.extend(items)
                continue

            best = self._pick_best(items)
            losers = [i for i in items if i is not best]
            resolved.append(best)
            conflicts.append(
                ConflictRecord(
                    subject=subject,
                    predicate=predicate,
                    winner=best,
                    losers=losers,
                    reason=self._reason(best, losers),
                )
            )

        return ResolvedEvidence(facts=resolved, conflicts=conflicts)

    @staticmethod
    def _has_distinct_temporal_windows(items: list[dict[str, Any]]) -> bool:
        windows = [(i.get("valid_from"), i.get("valid_to")) for i in items]
        # If every item carries an explicit temporal window and they differ,
        # treat them as distinct historical facts rather than a conflict.
        if all(w != (None, None) for w in windows):
            return len(set(windows)) > 1
        return False

    @staticmethod
    def _pick_best(items: list[dict[str, Any]]) -> dict[str, Any]:
        def sort_key(item: dict[str, Any]) -> tuple[int, float, str]:
            priority = int(item.get("priority", 0))
            confidence = float(item.get("confidence", 0.0))
            valid_from = item.get("valid_from") or ""
            return (priority, confidence, valid_from)

        return max(items, key=sort_key)

    @staticmethod
    def _reason(best: dict[str, Any], losers: list[dict[str, Any]]) -> str:
        if any(int(loss.get("priority", 0)) != int(best.get("priority", 0)) for loss in losers):
            return "higher_priority"
        if any(float(loss.get("confidence", 0.0)) != float(best.get("confidence", 0.0)) for loss in losers):
            return "higher_confidence"
        return "newer_valid_info"
