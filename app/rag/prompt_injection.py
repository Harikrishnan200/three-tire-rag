"""Best-effort heuristic prompt-injection detector for retrieved document content.

This is NOT a guarantee of safety. It flags common injection phrasing so the
system can log/annotate suspicious chunks; it does not remove or "solve"
prompt injection risk, which remains a known limitation (see README).
"""

from __future__ import annotations

import re

_SUSPICIOUS_PATTERNS = [
    r"ignore (all )?(the )?previous instructions",
    r"ignore (all )?(the )?above",
    r"disregard (all )?(the )?(previous|above)",
    r"you are now",
    r"new instructions:",
    r"system prompt",
    r"reveal your (system )?prompt",
    r"act as (if you are )?",
    r"do anything now",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in _SUSPICIOUS_PATTERNS]


def flag_prompt_injection(text: str) -> list[str]:
    """Return the list of matched suspicious phrases (best-effort, may miss
    novel phrasing and may false-positive on benign text)."""
    matches: list[str] = []
    for pattern in _COMPILED:
        if pattern.search(text):
            matches.append(pattern.pattern)
    return matches
