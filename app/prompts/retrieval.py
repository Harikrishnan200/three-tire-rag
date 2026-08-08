QUESTION_REWRITE_PROMPT = """Given the conversation history and a follow-up question, rewrite the
follow-up question as a standalone question that contains all necessary context.
Return ONLY the rewritten question, nothing else.

History:
{history}

Follow-up question: {question}

Standalone question:"""
