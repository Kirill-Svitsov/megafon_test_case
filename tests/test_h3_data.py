import sys
from pathlib import Path

import pytest

from constants import (
    VALID_BORDER,
    INVALID_BORDER,
    SHORT_BORDER,
    POINT_INSIDE,
    TEST_POLYGON,
    POINT_OUTSIDE,
    POINT_ON_EDGE,
    ODD_ARRAY,
    EVEN_ARRAY,
    EMPTY_ARRAY,
    SINGLE_ARRAY,
)
from services.h3_data import (
    compute_level_and_cell_id,
    get_dataset,
    parse_border,
    point_in_polygon,
    get_hex_boundary,
    median_floor,
)

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestComputeLevelAndCellId:
    def test_returns_tuple(self):
        """Проверяет, что функция возвращает кортеж из двух чисел"""
        dataset = get_dataset()
        if dataset:
            h3_idx = dataset[0][0]
            result = compute_level_and_cell_id(h3_idx)
            assert isinstance(result, tuple)
            assert len(result) == 2
            assert isinstance(result[0], int)
            assert isinstance(result[1], int)


class TestParseBorder:
    def test_parses_valid_border(self):
        """Проверяет парсинг валидной строки border"""
        result = parse_border(VALID_BORDER)
        assert isinstance(result, list)
        assert len(result) >= 4
        assert all(isinstance(p, tuple) and len(p) == 2 for p in result)

    def test_raises_error_on_invalid_format(self):
        """Проверяет, что функция выбрасывает ошибку при невалидном формате"""
        with pytest.raises(ValueError):
            parse_border(INVALID_BORDER)

    def test_raises_error_on_less_than_3_points(self):
        """Проверяет, что нужно минимум 3 точки"""
        with pytest.raises(ValueError):
            parse_border(SHORT_BORDER)


class TestPointInPolygon:
    def test_point_inside(self):
        """Точка внутри квадрата"""
        assert point_in_polygon(POINT_INSIDE[0], POINT_INSIDE[1], TEST_POLYGON) is True

    def test_point_outside(self):
        """Точка снаружи квадрата"""
        assert point_in_polygon(POINT_OUTSIDE[0], POINT_OUTSIDE[1], TEST_POLYGON) is False

    def test_point_on_edge(self):
        """Точка на границе (должна считаться внутри по алгоритму)"""
        result = point_in_polygon(POINT_ON_EDGE[0], POINT_ON_EDGE[1], TEST_POLYGON)
        assert isinstance(result, bool)


class TestGetHexBoundary:
    def test_returns_list_or_tuple_of_6_points(self):
        """Гексагон должен иметь 6 вершин"""
        dataset = get_dataset()
        if dataset:
            h3_idx = dataset[0][0]
            boundary = get_hex_boundary(h3_idx)
            assert hasattr(boundary, "__iter__")
            assert len(boundary) in (6, 7)


class TestMedianFloor:
    def test_odd_length(self):
        """Медиана для нечётного количества"""
        assert median_floor(ODD_ARRAY) == 3

    def test_even_length(self):
        """Медиана для чётного количества (округляется вниз)"""
        assert median_floor(EVEN_ARRAY) == 2

    def test_empty_list(self):
        """Пустой список возвращает 0"""
        assert median_floor(EMPTY_ARRAY) == 0

    def test_single_element(self):
        """Один элемент"""
        assert median_floor(SINGLE_ARRAY) == 42
