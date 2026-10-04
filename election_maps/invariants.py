"""Reusable analytical integrity checks for election-map pipelines."""

from __future__ import annotations

from collections.abc import Mapping, Sequence


def assert_vote_conservation(
    source: Mapping[str, float],
    allocated: Mapping[str, float],
    *,
    atol: float = 0.5,
) -> None:
    """Raise when candidate totals change during geographic allocation."""
    for candidate in sorted(set(source) | set(allocated)):
        difference = float(source.get(candidate, 0)) - float(allocated.get(candidate, 0))
        if abs(difference) > atol:
            raise ValueError(
                f"Vote conservation failed for {candidate}: difference {difference:g} "
                f"(source={float(source.get(candidate, 0)):g}, "
                f"allocated={float(allocated.get(candidate, 0)):g})"
            )


def assert_join_cardinality(frame, keys: Sequence[str], relationship: str) -> None:
    """Validate the observable key cardinality of a joined frame."""
    valid = {"one_to_one", "one_to_many", "many_to_one", "many_to_many"}
    if relationship not in valid:
        raise ValueError(f"Unknown join relationship {relationship!r} for keys {list(keys)!r}")
    missing = [key for key in keys if key not in frame.columns]
    if missing:
        raise ValueError(
            f"Join cardinality {relationship} cannot be checked; missing keys {missing!r}"
        )
    if relationship == "one_to_one" and frame.duplicated(list(keys), keep=False).any():
        examples = frame.loc[frame.duplicated(list(keys), keep=False), list(keys)].head(3)
        raise ValueError(
            f"Join cardinality {relationship} violated for keys {list(keys)!r}: "
            f"{examples.to_dict('records')}"
        )
