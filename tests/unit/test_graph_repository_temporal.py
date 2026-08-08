from datetime import datetime

import pytest

from app.graph.models import GraphFact
from app.graph.repository import NetworkXGraphRepository


@pytest.mark.asyncio
async def test_temporal_query_returns_historical_fact_for_past_date() -> None:
    repo = NetworkXGraphRepository()
    await repo.add_fact(
        GraphFact(
            id="1",
            subject="Microsoft",
            predicate="ceo",
            object="Satya Nadella",
            priority=100,
            source="curated",
            valid_from=datetime(2014, 2, 4),
            valid_to=None,
        )
    )
    await repo.add_fact(
        GraphFact(
            id="2",
            subject="Microsoft",
            predicate="ceo",
            object="Steve Ballmer",
            priority=50,
            source="curated",
            valid_from=datetime(2000, 1, 13),
            valid_to=datetime(2014, 2, 4),
        )
    )

    current_facts = await repo.get_facts_for_entity("Microsoft", at=None)
    current_objects = {f.object for f in current_facts}
    assert "Satya Nadella" in current_objects
    assert "Steve Ballmer" not in current_objects

    historical_facts = await repo.get_facts_for_entity("Microsoft", at=datetime(2010, 6, 1))
    historical_objects = {f.object for f in historical_facts}
    assert "Steve Ballmer" in historical_objects
    assert "Satya Nadella" not in historical_objects


@pytest.mark.asyncio
async def test_historical_fact_does_not_override_current_fact_in_current_query() -> None:
    repo = NetworkXGraphRepository()
    await repo.add_fact(
        GraphFact(
            id="1",
            subject="Microsoft",
            predicate="ceo",
            object="Satya Nadella",
            priority=100,
            valid_to=None,
        )
    )
    await repo.add_fact(
        GraphFact(
            id="2",
            subject="Microsoft",
            predicate="ceo",
            object="Steve Ballmer",
            priority=50,
            valid_to=datetime(2014, 2, 4),
        )
    )
    facts = await repo.get_facts_for_entity("Microsoft", at=None)
    objects = {f.object for f in facts}
    assert objects == {"Satya Nadella"}
