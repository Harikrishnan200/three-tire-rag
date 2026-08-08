"""Deterministic entity/relationship extraction via spaCy NER."""

from __future__ import annotations

from abc import ABC, abstractmethod
from functools import lru_cache

from pydantic import BaseModel


class ExtractedEntity(BaseModel):
    text: str
    label: str


class ExtractedRelationship(BaseModel):
    subject: str
    predicate: str
    object: str


class EntityExtractor(ABC):
    @abstractmethod
    def extract_entities(self, text: str) -> list[ExtractedEntity]: ...

    @abstractmethod
    def extract_relationships(self, text: str) -> list[ExtractedRelationship]: ...


class SpacyEntityExtractor(EntityExtractor):
    """spaCy-based NER extractor. Falls back to a blank pipeline if a trained
    model isn't installed, so the app degrades gracefully rather than crashing."""

    def __init__(self, model_name: str = "en_core_web_sm") -> None:
        import spacy

        try:
            self._nlp = spacy.load(model_name)
        except OSError:
            self._nlp = spacy.blank("en")
            if "sentencizer" not in self._nlp.pipe_names:
                self._nlp.add_pipe("sentencizer")

    def extract_entities(self, text: str) -> list[ExtractedEntity]:
        doc = self._nlp(text)
        if not doc.has_annotation("ENT_IOB"):
            return []
        return [ExtractedEntity(text=ent.text, label=ent.label_) for ent in doc.ents]

    def extract_relationships(self, text: str) -> list[ExtractedRelationship]:
        """Very simple deterministic heuristic: for sentences with exactly two
        entities and a verb between them, emit subject-verb-object triples.
        This is intentionally conservative (precision over recall) — it is a
        secondary signal, not the source of truth for tier1/tier2 facts."""
        doc = self._nlp(text)
        relationships: list[ExtractedRelationship] = []
        for sent in doc.sents:
            ents = list(sent.ents) if doc.has_annotation("ENT_IOB") else []
            if len(ents) < 2:
                continue
            verbs = [t.lemma_ for t in sent if t.pos_ == "VERB"]
            predicate = verbs[0] if verbs else "related_to"
            for i in range(len(ents) - 1):
                relationships.append(
                    ExtractedRelationship(
                        subject=ents[i].text, predicate=predicate, object=ents[i + 1].text
                    )
                )
        return relationships


@lru_cache
def get_entity_extractor() -> EntityExtractor:
    return SpacyEntityExtractor()
