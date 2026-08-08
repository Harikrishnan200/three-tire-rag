from app.rag.conflict_resolver import ConflictResolver


def test_tier1_overrides_tier2() -> None:
    resolver = ConflictResolver()
    evidence = [
        {
            "tier": 1,
            "priority": 100,
            "subject": "Microsoft",
            "predicate": "ceo",
            "object": "Satya Nadella",
            "confidence": 1.0,
            "valid_from": None,
            "valid_to": None,
        },
        {
            "tier": 2,
            "priority": 50,
            "subject": "Microsoft",
            "predicate": "ceo",
            "object": "Steve Ballmer",
            "confidence": 1.0,
            "valid_from": "2000-01-01",
            "valid_to": "2014-02-01",
        },
    ]
    resolved = resolver.resolve(evidence)
    # Distinct temporal windows -> both preserved (not a "conflict" to collapse),
    # but when asked for "current" (no window on tier1), tier1 must still be present
    # and, if not temporally distinct, tier1 wins.
    objects = {f["object"] for f in resolved.facts}
    assert "Satya Nadella" in objects


def test_tier1_wins_when_no_temporal_distinction() -> None:
    resolver = ConflictResolver()
    evidence = [
        {"tier": 1, "priority": 100, "subject": "Microsoft", "predicate": "ceo", "object": "Satya Nadella", "confidence": 1.0, "valid_from": None, "valid_to": None},
        {"tier": 2, "priority": 50, "subject": "Microsoft", "predicate": "ceo", "object": "Steve Ballmer", "confidence": 1.0, "valid_from": None, "valid_to": None},
    ]
    resolved = resolver.resolve(evidence)
    assert len(resolved.facts) == 1
    assert resolved.facts[0]["object"] == "Satya Nadella"
    assert len(resolved.conflicts) == 1
    assert resolved.conflicts[0].reason == "higher_priority"


def test_tier2_overrides_tier3() -> None:
    resolver = ConflictResolver()
    evidence = [
        {"tier": 2, "priority": 50, "subject": "Microsoft", "predicate": "ceo", "object": "Steve Ballmer", "confidence": 1.0, "valid_from": None, "valid_to": None},
        {"tier": 3, "priority": 10, "subject": "Microsoft", "predicate": "ceo", "object": "Bill Gates", "confidence": 0.4, "valid_from": None, "valid_to": None},
    ]
    resolved = resolver.resolve(evidence)
    assert len(resolved.facts) == 1
    assert resolved.facts[0]["object"] == "Steve Ballmer"
    assert resolved.conflicts[0].reason == "higher_priority"


def test_tie_on_priority_uses_confidence() -> None:
    resolver = ConflictResolver()
    evidence = [
        {"tier": 2, "priority": 50, "subject": "X", "predicate": "p", "object": "A", "confidence": 0.9, "valid_from": None, "valid_to": None},
        {"tier": 2, "priority": 50, "subject": "X", "predicate": "p", "object": "B", "confidence": 0.5, "valid_from": None, "valid_to": None},
    ]
    resolved = resolver.resolve(evidence)
    assert resolved.facts[0]["object"] == "A"
    assert resolved.conflicts[0].reason == "higher_confidence"


def test_non_conflicting_facts_are_not_merged_away() -> None:
    resolver = ConflictResolver()
    evidence = [
        {"tier": 1, "priority": 100, "subject": "Apple", "predicate": "ceo", "object": "Tim Cook", "confidence": 1.0, "valid_from": None, "valid_to": None},
        {"tier": 1, "priority": 100, "subject": "Microsoft", "predicate": "ceo", "object": "Satya Nadella", "confidence": 1.0, "valid_from": None, "valid_to": None},
    ]
    resolved = resolver.resolve(evidence)
    assert len(resolved.facts) == 2
    assert len(resolved.conflicts) == 0
