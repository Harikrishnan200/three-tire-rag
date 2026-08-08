from __future__ import annotations

from app.rag.entity_extraction import EntityExtractor, ExtractedEntity, ExtractedRelationship


class FakeEntityExtractor(EntityExtractor):
    """Keyword-matches a known vocabulary of entities instead of running spaCy
    NER (which requires a downloaded model we don't have in this environment)."""

    def __init__(self, vocabulary: list[str] | None = None) -> None:
        self._vocabulary = vocabulary or [
            "Microsoft",
            "Apple",
            "Google",
            "OpenAI",
            "Tim Cook",
            "Satya Nadella",
            "Sundar Pichai",
            "Sam Altman",
            "Steve Ballmer",
        ]

    def extract_entities(self, text: str) -> list[ExtractedEntity]:
        found = [ExtractedEntity(text=name, label="ORG_OR_PERSON") for name in self._vocabulary if name.lower() in text.lower()]
        return found

    def extract_relationships(self, text: str) -> list[ExtractedRelationship]:
        return []
