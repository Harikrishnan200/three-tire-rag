"""Seed the graph store and a sample document with a demo tech-company KB.

Demonstrates the core value proposition: deterministic tier1/tier2 conflict
resolution + temporal correctness.

  "who is Microsoft's current CEO"  -> Satya Nadella (tier1, priority 100)
  "who was Microsoft's CEO in 2010" -> Steve Ballmer (tier2, priority 50, valid_to=2014)

Run with: .venv/bin/python scripts/seed_data.py
This seeds the in-memory graph repository for the current process only; in a
real deployment this would target the shared graph store (or be re-run against
a persistent Neo4j backend once that's wired in).
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from app.graph.container import get_graph_repository
from app.graph.models import GraphFact

NOW = datetime.now(timezone.utc)


def _fact(**kwargs) -> GraphFact:
    kwargs.setdefault("id", "")
    kwargs.setdefault("created_at", NOW)
    kwargs.setdefault("updated_at", NOW)
    return GraphFact(**kwargs)


FACTS: list[GraphFact] = [
    # --- Tier 1: authoritative current facts (priority 100) ---
    _fact(subject="Microsoft", predicate="ceo", object="Satya Nadella", priority=100, source="company_filing", confidence=1.0),
    _fact(subject="Apple", predicate="ceo", object="Tim Cook", priority=100, source="company_filing", confidence=1.0),
    _fact(subject="Google", predicate="ceo", object="Sundar Pichai", priority=100, source="company_filing", confidence=1.0),
    _fact(subject="OpenAI", predicate="ceo", object="Sam Altman", priority=100, source="company_filing", confidence=1.0),
    _fact(subject="Apple", predicate="founded_by", object="Steve Jobs", priority=100, source="curated_kb", confidence=1.0),
    _fact(subject="Microsoft", predicate="founded_by", object="Bill Gates", priority=100, source="curated_kb", confidence=1.0),
    _fact(subject="Google", predicate="founded_by", object="Larry Page", priority=100, source="curated_kb", confidence=1.0),
    _fact(subject="OpenAI", predicate="founded_by", object="Sam Altman", priority=100, source="curated_kb", confidence=1.0),
    _fact(subject="Apple", predicate="headquartered_in", object="Cupertino", priority=100, source="curated_kb", confidence=1.0),
    _fact(subject="Microsoft", predicate="headquartered_in", object="Redmond", priority=100, source="curated_kb", confidence=1.0),
    _fact(subject="Google", predicate="headquartered_in", object="Mountain View", priority=100, source="curated_kb", confidence=1.0),
    _fact(subject="OpenAI", predicate="headquartered_in", object="San Francisco", priority=100, source="curated_kb", confidence=1.0),
    _fact(subject="Microsoft", predicate="partnered_with", object="OpenAI", priority=100, source="curated_kb", confidence=1.0),
    _fact(subject="Google", predicate="owns", object="DeepMind", priority=100, source="curated_kb", confidence=1.0),
    _fact(subject="Microsoft", predicate="employs", object="Satya Nadella", priority=100, source="curated_kb", confidence=1.0),
    _fact(subject="OpenAI", predicate="released", object="ChatGPT", priority=100, source="curated_kb", confidence=1.0),
    # --- Tier 2: historical/statistical facts (priority 50), with temporal validity ---
    _fact(
        subject="Microsoft",
        predicate="ceo",
        object="Steve Ballmer",
        priority=50,
        source="historical_record",
        confidence=0.95,
        valid_from=datetime(2000, 1, 13, tzinfo=timezone.utc),
        valid_to=datetime(2014, 2, 4, tzinfo=timezone.utc),
    ),
    _fact(
        subject="Apple",
        predicate="ceo",
        object="Steve Jobs",
        priority=50,
        source="historical_record",
        confidence=0.95,
        valid_from=datetime(1997, 1, 1, tzinfo=timezone.utc),
        valid_to=datetime(2011, 8, 24, tzinfo=timezone.utc),
    ),
]


async def seed() -> None:
    repo = get_graph_repository()
    for fact in FACTS:
        await repo.add_fact(fact)
    print(f"Seeded {len(FACTS)} graph facts into the shared in-memory graph repository.")
    print("Demo queries:")
    print('  "Who is Microsoft\'s current CEO?" -> Satya Nadella (tier1)')
    print('  "Who was Microsoft\'s CEO in 2010?" -> Steve Ballmer (tier2, valid_to=2014-02-04)')


if __name__ == "__main__":
    asyncio.run(seed())
