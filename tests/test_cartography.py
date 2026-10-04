import pytest

from election_maps.cartography import ALABAMA_METROS, MIN_TYPE_PT, blend_hex


def test_minimum_type_roles_are_publication_safe():
    assert MIN_TYPE_PT["source"] >= 7.0
    assert MIN_TYPE_PT["results"] >= 6.5


def test_alabama_metros_are_complete():
    assert set(ALABAMA_METROS) == {"HUNTSVILLE", "BIRMINGHAM", "MONTGOMERY", "MOBILE"}


def test_blend_hex_reaches_floor_and_base():
    assert blend_hex("#000000", 0, "#FFFFFF") == pytest.approx((1, 1, 1))
    assert blend_hex("#000000", 1, "#FFFFFF") == pytest.approx((0, 0, 0))
