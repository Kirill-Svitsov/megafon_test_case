# constants.py
# ============================================================
# ГЕОГРАФИЧЕСКИЕ КОНСТАНТЫ
# ============================================================
CENTER_LAT = 56.0
CENTER_LON = 38.0
RADIUS_METERS = 7000
RESOLUTION = 12

# ============================================================
# МАТЕМАТИЧЕСКИЕ КОНСТАНТЫ
# ============================================================
R = 6371000  # Радиус Земли в метрах
METERS_PER_KILOMETER = 1000
MS_PER_SECOND = 1000
BYTES_PER_KB = 1024
KB_PER_MB = 1024

# ============================================================
# КОНСТАНТЫ H3
# ============================================================
K_RINGS = 500
K_RINGS_BUFFER = 100
DEFAULT_HEX_SIZE_M = 50

CELL_SIZES = {
    0: 11000000,
    1: 4000000,
    2: 1500000,
    3: 570000,
    4: 210000,
    5: 72000,
    6: 25000,
    7: 8900,
    8: 3100,
    9: 1100,
    10: 390,
    11: 140,
    12: 50,
    13: 18,
    14: 6.5,
    15: 2.3,
}

# ============================================================
# КОНСТАНТЫ API
# ============================================================
CACHE_MAX_SIZE = 128

DEFAULT_LIMIT = 100
MAX_LIMIT = 10000

DEFAULT_BBOX_LIMIT = 1000
MAX_BBOX_LIMIT = 10000

MIN_RESOLUTION = 0
MAX_RESOLUTION = 12

# ============================================================
# КОНСТАНТЫ ДЛЯ ЛОГГЕРА
# ============================================================
RESET = "\033[0m"

LEVEL_COLORS = {
    "DEBUG": "\033[36m",
    "INFO": "\033[32m",
    "WARNING": "\033[33m",
    "ERROR": "\033[31m",
    "CRITICAL": "\033[91m",
}

# ============================================================
# ТЕСТОВЫЕ КОНСТАНТЫ
# ============================================================
THREE_POINTS = 3

# Полигоны для тестов
SAMPLE_POLYGON = "56.1/37.9,56.1/38.1,55.9/38.1,55.9/37.9,56.1/37.9"
SMALL_POLYGON = "56.01/37.99,56.01/38.00,55.99/38.00,55.99/37.99,56.01/37.99"
VALID_BORDER = SAMPLE_POLYGON
INVALID_BORDER = "56.1;37.9,56.1;38.1"
SHORT_BORDER = "56.1/37.9,56.1/38.1"

# Тестовый квадрат для point_in_polygon
TEST_POLYGON = [(0, 0), (0, 10), (10, 10), (10, 0), (0, 0)]
POINT_INSIDE = (5, 5)
POINT_OUTSIDE = (15, 15)
POINT_ON_EDGE = (5, 0)

# Тестовые массивы для median_floor
ODD_ARRAY = [1, 3, 5]
EVEN_ARRAY = [1, 2, 3, 4]
SINGLE_ARRAY = [42]
EMPTY_ARRAY = []

# HTTP статус коды
HTTP_200_OK = 200
HTTP_400_BAD_REQUEST = 400
HTTP_422_UNPROCESSABLE = 422

# H3 индексы для тестов
VALID_HEX = "8c11aa6483601ff"
INVALID_HEX = "invalid"

# Разрешения для тестов
VALID_RESOLUTION = 0
INVALID_RESOLUTION = 20
TEST_RESOLUTION_12 = 12

# Пагинация для тестов
PAGINATION_LIMIT = 10
PAGINATION_OFFSET = 0
BBOX_PAGINATION_LIMIT = 100

# CORS для тестов
CORS_ORIGIN = "http://localhost:3000"

# Median floor тесты
ODD_LIST = [10, 20, 30]
ODD_EXPECTED = 20
EVEN_LIST = [10, 20, 30, 40]
EVEN_EXPECTED = 20
EMPTY_LIST = []
EMPTY_EXPECTED = 0
SINGLE_LIST = [100]
SINGLE_EXPECTED = 100
