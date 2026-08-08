"""Process-wide singleton accessor for the graph repository.

The in-memory NetworkX implementation must be shared across requests within a
process (it's the "database"), so we use an lru_cache factory rather than a
bare global, keeping it swappable/testable via dependency overrides.
"""

from functools import lru_cache

from app.graph.repository import GraphRepository, NetworkXGraphRepository


@lru_cache
def get_graph_repository() -> GraphRepository:
    return NetworkXGraphRepository()
