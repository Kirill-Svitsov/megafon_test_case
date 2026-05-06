import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))  # noqa

from constants import SAMPLE_POLYGON, SMALL_POLYGON  # noqa

import pytest  # noqa
from fastapi.testclient import TestClient  # noqa

from main import app  # noqa


@pytest.fixture
def client():
    """Тестовый клиент FastAPI app"""
    return TestClient(app)


@pytest.fixture
def sample_polygon():
    """Полигон для тестов"""
    return SAMPLE_POLYGON


@pytest.fixture
def small_polygon():
    """Небольшой полигон для тестов"""
    return SMALL_POLYGON
