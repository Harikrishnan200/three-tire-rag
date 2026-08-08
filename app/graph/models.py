from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class GraphFact(BaseModel):
    """A single subject-predicate-object graph fact with provenance and temporal validity."""

    id: str
    subject: str
    predicate: str
    object: str
    context: str | None = None
    source: str = "unknown"
    priority: int = 50  # 100 = tier1 authoritative, 50 = tier2 historical/statistical
    confidence: float = 1.0
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def is_valid_at(self, at: datetime | None) -> bool:
        if at is None:
            # "current" query: fact must have no end date (still valid)
            return self.valid_to is None
        if self.valid_from is not None and at < self.valid_from:
            return False
        if self.valid_to is not None and at > self.valid_to:
            return False
        return True

    def as_evidence(self, tier: int) -> dict[str, Any]:
        return {
            "tier": tier,
            "priority": self.priority,
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object,
            "source": self.source,
            "confidence": self.confidence,
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_to": self.valid_to.isoformat() if self.valid_to else None,
            "fact_id": self.id,
        }
