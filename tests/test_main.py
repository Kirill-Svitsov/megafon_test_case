import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))  # noqa

from constants import (  # noqa
    VALID_HEX,
    HTTP_200_OK,
    INVALID_HEX,
    HTTP_400_BAD_REQUEST,
    VALID_RESOLUTION,
    INVALID_RESOLUTION,
    HTTP_422_UNPROCESSABLE,
    PAGINATION_LIMIT,
    PAGINATION_OFFSET,
    TEST_RESOLUTION_12,
    BBOX_PAGINATION_LIMIT,
    CORS_ORIGIN,
)  # noqa


class TestHexEndpoint:
    def test_hex_valid(self, client):
        """Проверяет /hex с валидным индексом"""
        response = client.get("/hex", params={"hex": VALID_HEX})
        assert response.status_code == HTTP_200_OK

    def test_hex_invalid(self, client):
        """Проверяет /hex с невалидным индексом"""
        response = client.get("/hex", params={"hex": INVALID_HEX})
        assert response.status_code == HTTP_400_BAD_REQUEST

    def test_hex_found(self, client):
        """Проверяет /hex с существующим индексом из датасета"""
        from services.h3_data import get_dataset

        dataset = get_dataset()
        if dataset:
            existing_hex = dataset[0][0]
            response = client.get("/hex", params={"hex": existing_hex})
            assert response.status_code == HTTP_200_OK


class TestAvgEndpoint:
    def test_avg_valid_resolution(self, client):
        """Проверяет /avg с валидным resolution"""
        response = client.get("/avg", params={"resolution": VALID_RESOLUTION})
        assert response.status_code == HTTP_200_OK

    def test_avg_invalid_resolution(self, client):
        """Проверяет /avg с невалидным resolution"""
        response = client.get("/avg", params={"resolution": INVALID_RESOLUTION})
        assert response.status_code in (HTTP_400_BAD_REQUEST, HTTP_422_UNPROCESSABLE)

    def test_avg_with_pagination(self, client):
        """Проверяет /avg с пагинацией"""
        response = client.get(
            "/avg",
            params={
                "resolution": VALID_RESOLUTION,
                "limit": PAGINATION_LIMIT,
                "offset": PAGINATION_OFFSET,
            },
        )
        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert "has_next" in data
        assert "data" in data

    def test_avg_resolution_12(self, client):
        """Проверяет /avg с resolution 12"""
        response = client.get("/avg", params={"resolution": TEST_RESOLUTION_12})
        assert response.status_code == HTTP_200_OK


class TestBboxEndpoint:
    def test_bbox_valid_polygon(self, client, sample_polygon):
        """Проверяет /bbox с валидным полигоном"""
        response = client.get("/bbox", params={"border": sample_polygon})
        assert response.status_code == HTTP_200_OK

    def test_bbox_invalid_polygon(self, client):
        """Проверяет /bbox с невалидным полигоном"""
        response = client.get("/bbox", params={"border": "invalid"})
        assert response.status_code == HTTP_400_BAD_REQUEST

    def test_bbox_with_pagination(self, client, sample_polygon):
        """Проверяет /bbox с пагинацией"""
        response = client.get(
            "/bbox",
            params={
                "border": sample_polygon,
                "limit": BBOX_PAGINATION_LIMIT,
                "offset": PAGINATION_OFFSET,
            },
        )
        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert "has_next" in data
        assert "data" in data


class TestBboxKmlEndpoint:
    def test_bbox_kml_download(self, client, small_polygon):
        """Проверяет /bbox_kml - скачивание KML файла"""
        response = client.get("/bbox_kml", params={"border": small_polygon})
        assert response.status_code == HTTP_200_OK
        assert response.headers["content-type"] == "application/vnd.google-earth.kml+xml"
        assert "Content-Disposition" in response.headers
        assert "hexagons.kml" in response.headers["Content-Disposition"]

    def test_bbox_kml_invalid_polygon(self, client):
        """Проверяет /bbox_kml с невалидным полигоном"""
        response = client.get("/bbox_kml", params={"border": "invalid"})
        assert response.status_code == HTTP_400_BAD_REQUEST


class TestCors:
    def test_cors_headers(self, client):
        """Проверяет наличие CORS заголовков"""
        response = client.options(
            "/hex",
            headers={
                "Origin": CORS_ORIGIN,
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == HTTP_200_OK
        assert "access-control-allow-origin" in response.headers
