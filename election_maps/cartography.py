"""Shared publication constants and pure color helpers."""

from __future__ import annotations

from matplotlib.colors import to_rgb

PAPER = "#F4F1E9"
PANEL = "#FBFAF6"
HEADER = "#27343C"
INK = "#182329"
MUTED = "#677178"
BORDER = "#27343C"
SERIF = "Nimbus Roman"
SANS = "Nimbus Sans Narrow"

ALABAMA_METROS = {
    "HUNTSVILLE": (-86.5861, 34.7304),
    "BIRMINGHAM": (-86.8025, 33.5207),
    "MONTGOMERY": (-86.3000, 32.3777),
    "MOBILE": (-88.0431, 30.6954),
}

MIN_TYPE_PT = {
    "source": 7.0,
    "results": 6.5,
    "status": 6.5,
    "legend": 7.0,
}


def blend_hex(base: str, strength: float, floor: str = "#E8EDF0") -> tuple[float, float, float]:
    """Blend a base color against a light floor at a bounded strength."""
    if not 0 <= strength <= 1:
        raise ValueError(f"strength must be between 0 and 1, got {strength}")
    base_rgb = to_rgb(base)
    floor_rgb = to_rgb(floor)
    return tuple(channel_floor * (1 - strength) + channel_base * strength
                 for channel_base, channel_floor in zip(base_rgb, floor_rgb))
