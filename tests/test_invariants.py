import pandas as pd
import pytest

from election_maps.invariants import assert_join_cardinality, assert_vote_conservation


def test_vote_conservation_names_candidate_difference():
    with pytest.raises(ValueError, match=r"sparks.*difference 2"):
        assert_vote_conservation({"sparks": 10}, {"sparks": 8})


def test_vote_conservation_accepts_rounding_tolerance():
    assert_vote_conservation({"sparks": 10}, {"sparks": 9.6})


def test_one_to_one_cardinality_names_keys_and_relationship():
    frame = pd.DataFrame({"precinct": ["A", "A"]})
    with pytest.raises(ValueError, match=r"one_to_one.*precinct"):
        assert_join_cardinality(frame, ["precinct"], "one_to_one")


def test_one_to_one_cardinality_accepts_unique_keys():
    assert_join_cardinality(pd.DataFrame({"precinct": ["A", "B"]}), ["precinct"], "one_to_one")
