from constants import (
    ODD_LIST,
    ODD_EXPECTED,
    EVEN_LIST,
    EVEN_EXPECTED,
    EMPTY_EXPECTED,
    EMPTY_LIST,
    SINGLE_LIST,
    SINGLE_EXPECTED,
)
from services.h3_data import median_floor


class TestMedianFloor:
    def test_odd(self):
        assert median_floor(ODD_LIST) == ODD_EXPECTED

    def test_even(self):
        assert median_floor(EVEN_LIST) == EVEN_EXPECTED

    def test_empty(self):
        assert median_floor(EMPTY_LIST) == EMPTY_EXPECTED

    def test_single(self):
        assert median_floor(SINGLE_LIST) == SINGLE_EXPECTED
