from __future__ import annotations

import re
import time
from datetime import datetime
from typing import Any

from app.core.exceptions import RetrievalError
from app.db.repositories import ConversationRepository, MessageRepository
from app.embeddings.provider import EmbeddingProvider
from app.graph.repository import GraphRepository
from app.llm.provider import LLMProvider
from app.prompts.generation import GENERATION_USER_PROMPT_TEMPLATE, build_context_block
from app.prompts.system import SYSTEM_PROMPT
from app.rag.conflict_resolver import ConflictResolver
from app.rag.entity_extraction import EntityExtractor
from app.rag.prompt_injection import flag_prompt_injection
from app.vector.repository import VectorRepository

_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")


def _extract_query_time(question: str) -> datetime | None:
    """Very small heuristic: if the question mentions a specific past year and
    doesn't say "current"/"now", treat it as a point-in-time query."""
    if re.search(r"\bcurrent(ly)?\b|\bnow\b|\btoday\b", question, re.IGNORECASE):
        return None
    match = _YEAR_RE.search(question)
    if match:
        year = int(match.group(0))
        return datetime(year, 12, 31)
    return None


class RAGService:
    def __init__(
        self,
        graph_repository: GraphRepository,
        vector_repository: VectorRepository,
        embedding_provider: EmbeddingProvider,
        llm_provider: LLMProvider,
        entity_extractor: EntityExtractor,
        conversation_repository: ConversationRepository,
        message_repository: MessageRepository,
        conflict_resolver: ConflictResolver | None = None,
        model_name: str = "unknown",
    ) -> None:
        self._graph = graph_repository
        self._vector = vector_repository
        self._embeddings = embedding_provider
        self._llm = llm_provider
        self._extractor = entity_extractor
        self._conversations = conversation_repository
        self._messages = message_repository
        self._resolver = conflict_resolver or ConflictResolver()
        self._model_name = model_name

    async def answer_question(
        self, user_id: str, conversation_id: str, question: str
    ) -> dict[str, Any]:
        start = time.perf_counter()

        await self._messages.list_for_conversation(conversation_id)  # loaded for future rewrite use
        standalone_question = question  # single-turn rewrite kept simple/deterministic

        at = _extract_query_time(standalone_question)

        entities = self._extractor.extract_entities(standalone_question)
        entity_texts = [e.text for e in entities] or [standalone_question]

        tier1_evidence: list[dict[str, Any]] = []
        tier2_evidence: list[dict[str, Any]] = []
        try:
            for entity_text in entity_texts:
                facts = await self._graph.get_facts_for_entity(entity_text, at=at)
                for fact in facts:
                    ev = fact.as_evidence(tier=1 if fact.priority >= 100 else 2)
                    if fact.priority >= 100:
                        tier1_evidence.append(ev)
                    else:
                        tier2_evidence.append(ev)
        except Exception as exc:  # pragma: no cover
            raise RetrievalError(f"Graph retrieval failed: {exc}") from exc

        tier3_evidence: list[dict[str, Any]] = []
        injection_flags: list[str] = []
        try:
            query_embedding = self._embeddings.embed_text(standalone_question)
            hits = await self._vector.search(query_embedding, user_id=user_id, limit=5)
            for hit in hits:
                flags = flag_prompt_injection(hit.text)
                injection_flags.extend(flags)
                tier3_evidence.append(
                    {
                        "tier": 3,
                        "priority": 10,
                        "subject": standalone_question,
                        "predicate": "mentioned_in",
                        "object": hit.text[:500],
                        "text": hit.text,
                        "source": f"document:{hit.document_id}",
                        "confidence": hit.score,
                        "document_id": hit.document_id,
                        "chunk_id": hit.chunk_id,
                        "page": hit.page,
                        "valid_from": None,
                        "valid_to": None,
                    }
                )
        except Exception as exc:  # pragma: no cover
            raise RetrievalError(f"Vector retrieval failed: {exc}") from exc

        all_evidence = tier1_evidence + tier2_evidence + tier3_evidence
        resolved = self._resolver.resolve(all_evidence)

        context_block = build_context_block(resolved.facts)
        user_prompt = GENERATION_USER_PROMPT_TEMPLATE.format(
            context=context_block, question=standalone_question
        )

        answer = await self._llm.generate(SYSTEM_PROMPT, user_prompt)

        citations = self._build_citations(resolved.facts)

        latency_ms = int((time.perf_counter() - start) * 1000)

        user_message = await self._messages.add_message(conversation_id, "user", question)
        assistant_message = await self._messages.add_message(
            conversation_id, "assistant", answer, latency_ms=latency_ms, model=self._model_name
        )
        await self._messages.add_retrieval_event(
            assistant_message.id,
            tier_1=tier1_evidence,
            tier_2=tier2_evidence,
            tier_3=[{k: v for k, v in e.items() if k != "text"} for e in tier3_evidence],
            conflicts=[
                {
                    "subject": c.subject,
                    "predicate": c.predicate,
                    "winner": c.winner,
                    "losers": c.losers,
                    "reason": c.reason,
                }
                for c in resolved.conflicts
            ],
        )
        await self._messages.add_citations(assistant_message.id, citations)
        del user_message

        return {
            "answer": answer,
            "conversation_id": conversation_id,
            "citations": citations,
            "retrieval": {
                "tier_1": tier1_evidence,
                "tier_2": tier2_evidence,
                "tier_3": tier3_evidence,
            },
            "metadata": {"latency_ms": latency_ms, "model": self._model_name},
            "conflicts": resolved.conflicts,
            "injection_flags": injection_flags,
        }

    @staticmethod
    def _build_citations(evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
        citations: list[dict[str, Any]] = []
        for item in evidence:
            if item.get("tier") == 3:
                citations.append(
                    {
                        "source_type": "document",
                        "document_id": item.get("document_id"),
                        "chunk_id": item.get("chunk_id"),
                        "page": item.get("page"),
                        "tier": None,
                        "subject": None,
                        "predicate": None,
                        "object": None,
                    }
                )
            else:
                citations.append(
                    {
                        "source_type": "graph",
                        "document_id": None,
                        "chunk_id": None,
                        "page": None,
                        "tier": item.get("tier"),
                        "subject": item.get("subject"),
                        "predicate": item.get("predicate"),
                        "object": item.get("object"),
                    }
                )
        return citations
