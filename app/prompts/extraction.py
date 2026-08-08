ENTITY_EXTRACTION_PROMPT = """Extract named entities and relationships from the text below.
Return a JSON object with keys "entities" (list of {{text, label}}) and
"relationships" (list of {{subject, predicate, object}}). Only use information
explicitly present in the text.

TEXT:
{text}
"""
