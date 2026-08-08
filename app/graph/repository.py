"""GraphRepository abstraction over a graph fact store.

Implemented in-memory with networkx today; the interface is deliberately
storage-agnostic so a future Neo4j-backed implementation can be swapped in
without touching any app-layer code (services only depend on this ABC).
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import UTC, datetime

import networkx as nx

from app.graph.models import GraphFact


class GraphRepository(ABC):
    @abstractmethod
    async def add_fact(self, fact: GraphFact) -> GraphFact: ...

    @abstractmethod
    async def get_facts_for_entity(
        self, entity: str, at: datetime | None = None
    ) -> list[GraphFact]: ...

    @abstractmethod
    async def find_relationship(
        self, subject: str, predicate: str, at: datetime | None = None
    ) -> list[GraphFact]: ...

    @abstractmethod
    async def find_related_entities(self, entity: str) -> list[str]: ...

    @abstractmethod
    async def search_entities(self, query: str) -> list[str]: ...

    @abstractmethod
    async def search_relationships(
        self, query: str, at: datetime | None = None
    ) -> list[GraphFact]: ...

    @abstractmethod
    async def get_subgraph(self, entity: str, depth: int = 1) -> list[GraphFact]: ...

    @abstractmethod
    async def delete_fact(self, fact_id: str) -> None: ...

    @abstractmethod
    async def update_fact(self, fact_id: str, **updates: object) -> GraphFact | None: ...


def _norm(text: str) -> str:
    return text.strip().lower()


class NetworkXGraphRepository(GraphRepository):
    """In-memory MultiDiGraph-backed implementation. Not persisted across process restarts."""

    def __init__(self) -> None:
        self._graph: nx.MultiDiGraph = nx.MultiDiGraph()
        self._facts: dict[str, GraphFact] = {}

    async def add_fact(self, fact: GraphFact) -> GraphFact:
        if not fact.id:
            fact.id = str(uuid.uuid4())
        self._facts[fact.id] = fact
        self._graph.add_node(_norm(fact.subject), label=fact.subject)
        self._graph.add_node(_norm(fact.object), label=fact.object)
        self._graph.add_edge(_norm(fact.subject), _norm(fact.object), key=fact.id, fact_id=fact.id)
        return fact

    async def get_facts_for_entity(
        self, entity: str, at: datetime | None = None
    ) -> list[GraphFact]:
        key = _norm(entity)
        results = [
            f
            for f in self._facts.values()
            if (_norm(f.subject) == key or _norm(f.object) == key) and f.is_valid_at(at)
        ]
        return results

    async def find_relationship(
        self, subject: str, predicate: str, at: datetime | None = None
    ) -> list[GraphFact]:
        s, p = _norm(subject), _norm(predicate)
        return [
            f
            for f in self._facts.values()
            if _norm(f.subject) == s and _norm(f.predicate) == p and f.is_valid_at(at)
        ]

    async def find_related_entities(self, entity: str) -> list[str]:
        key = _norm(entity)
        if key not in self._graph:
            return []
        neighbors = set(self._graph.successors(key)) | set(self._graph.predecessors(key))
        return [self._graph.nodes[n].get("label", n) for n in neighbors]

    async def search_entities(self, query: str) -> list[str]:
        q = _norm(query)
        return [
            data.get("label", n)
            for n, data in self._graph.nodes(data=True)
            if q in _norm(data.get("label", n))
        ]

    async def search_relationships(self, query: str, at: datetime | None = None) -> list[GraphFact]:
        q = _norm(query)
        return [
            f
            for f in self._facts.values()
            if (q in _norm(f.subject) or q in _norm(f.predicate) or q in _norm(f.object))
            and f.is_valid_at(at)
        ]

    async def get_subgraph(self, entity: str, depth: int = 1) -> list[GraphFact]:
        key = _norm(entity)
        if key not in self._graph:
            return []
        visited = {key}
        frontier = {key}
        for _ in range(depth):
            next_frontier: set[str] = set()
            for node in frontier:
                next_frontier |= set(self._graph.successors(node)) | set(
                    self._graph.predecessors(node)
                )
            frontier = next_frontier - visited
            visited |= next_frontier
        return [
            f
            for f in self._facts.values()
            if _norm(f.subject) in visited or _norm(f.object) in visited
        ]

    async def delete_fact(self, fact_id: str) -> None:
        fact = self._facts.pop(fact_id, None)
        if fact is not None and self._graph.has_edge(
            _norm(fact.subject), _norm(fact.object), key=fact_id
        ):
            self._graph.remove_edge(_norm(fact.subject), _norm(fact.object), key=fact_id)

    async def update_fact(self, fact_id: str, **updates: object) -> GraphFact | None:
        fact = self._facts.get(fact_id)
        if fact is None:
            return None
        updated = fact.model_copy(update={**updates, "updated_at": datetime.now(UTC)})
        self._facts[fact_id] = updated
        return updated
