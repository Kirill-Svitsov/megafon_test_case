import h3
import math
from functools import lru_cache

from constants import (
    CENTER_LAT,
    CENTER_LON,
    RADIUS_METERS,
    RESOLUTION,
    R,
    METERS_PER_KILOMETER,
    K_RINGS,
    THREE_POINTS,
    CELL_SIZES,
    K_RINGS_BUFFER,
    DEFAULT_HEX_SIZE_M,
)
from utils.logger import logger


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Расстояние между точками на сфере в метрах (формула гаверсинуса)"""
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def compute_level_and_cell_id(h3_index: str):
    """Вычисляет level и cell_id по формулам из задания"""
    # Не стал выносить в константы, так как не ясно значение этих чисел
    h3_int = h3.str_to_int(h3_index)
    base = h3_int // 512
    level = (base % 74) - 120
    cell_id = (base % 100) + 1
    return level, cell_id


@lru_cache(maxsize=1)
def get_dataset():
    """Генерирует датасет гексагонов внутри круга"""
    logger.info(
        f"Генерация датасета: центр ({CENTER_LAT}, {CENTER_LON}), "
        f"радиус {RADIUS_METERS / METERS_PER_KILOMETER} км"
    )
    center_h3 = h3.latlng_to_cell(CENTER_LAT, CENTER_LON, RESOLUTION)
    logger.info(f"Сбор гексагонов в радиусе {K_RINGS} колец...")
    candidates = h3.grid_disk(center_h3, K_RINGS)
    logger.info(f"Найдено кандидатов: {len(candidates)}")
    dataset = []
    for h3_idx in candidates:
        lat, lon = h3.cell_to_latlng(h3_idx)
        dist = haversine_distance(CENTER_LAT, CENTER_LON, lat, lon)
        if dist < RADIUS_METERS:
            level, cell_id = compute_level_and_cell_id(h3_idx)
            dataset.append([h3_idx, level, cell_id])
    logger.info(f"Готово! {len(dataset)} гексагонов внутри круга")
    return dataset


def get_parent_hex(h3_index: str, resolution: int) -> str:
    """Возвращает родительский гексагон на указанном разрешении"""
    return h3.cell_to_parent(h3_index, resolution)


def median_floor(values):
    """Возвращает медиану массива, округлённую в меньшую сторону"""
    if not values:
        return 0
    sorted_values = sorted(values)
    n = len(sorted_values)
    return sorted_values[(n - 1) // 2]


def get_hex_boundary(h3_index: str):
    """
    Возвращает границы гексагона в виде списка вершин (lat, lon).
    """
    return h3.cell_to_boundary(h3_index)


def point_in_polygon(lat: float, lon: float, polygon) -> bool:
    """
    Проверяет, находится ли точка внутри полигона (ray casting algorithm).
    Args:
        lat: Широта точки
        lon: Долгота точки
        polygon: Список кортежей (lat, lon) вершин полигона
    Returns:
        True если точка внутри, False если снаружи
    """
    x, y = lon, lat
    inside = False
    n = len(polygon)
    for i in range(n):
        x1, y1 = polygon[i][1], polygon[i][0]
        x2, y2 = polygon[(i + 1) % n][1], polygon[(i + 1) % n][0]
        if ((y1 > y) != (y2 > y)) and (x < (x2 - x1) * (y - y1) / (y2 - y1) + x1):
            inside = not inside
    return inside


def is_completely_inside_polygon(h3_index: str, polygon) -> bool:
    """
    Проверяет, что все 6 вершин гексагона находятся внутри полигона.
    Args:
        h3_index: H3 индекс гексагона
        polygon: Список кортежей (lat, lon) вершин полигона
    Returns:
        True если весь гексагон внутри, False если есть пересечение границы
    """
    boundary = get_hex_boundary(h3_index)
    for lat, lon in boundary:
        if not point_in_polygon(lat, lon, polygon):
            return False
    return True


def parse_border(border_str: str):
    """
    Преобразует строку border в список координат полигона.
    Формат строки: "lat/lon,lat/lon,lat/lon,..."
    Args:
        border_str: Строка с координатами
    Returns:
        Список кортежей (широта, долгота) вершин полигона
    """
    coords = []
    for point in border_str.split(","):
        if not point.strip():
            continue
        lat_str, lon_str = point.split("/")
        lat = float(lat_str)
        lon = float(lon_str)
        coords.append((lat, lon))
    if len(coords) < THREE_POINTS:
        raise ValueError("Полигон должен содержать минимум 3 точки")
    # Замыкаем полигон, если не замкнут
    if coords[0] != coords[-1]:
        coords.append(coords[0])
    return coords


def get_hexagons_in_polygon(polygon, resolution: int):
    """
    Возвращает все гексагоны указанного разрешения, центры которых внутри полигона.
    Args:
        polygon: Список кортежей (lat, lon) вершин полигона
        resolution: Разрешение H3 (0-15)
    Returns:
        Множество H3 индексов
    """
    return set(h3.polygon_to_cells(polygon, resolution))


def get_bbox_polygon_center(polygon):
    """Находит центр bounding box полигона"""
    min_lat = min(p[0] for p in polygon)
    max_lat = max(p[0] for p in polygon)
    min_lon = min(p[1] for p in polygon)
    max_lon = max(p[1] for p in polygon)
    return (min_lat + max_lat) / 2, (min_lon + max_lon) / 2


def get_bbox_polygon_radius_meters(polygon, center_lat, center_lon):
    """Находит максимальное расстояние от центра до вершин полигона"""
    max_dist = 0
    for lat, lon in polygon:
        dist = haversine_distance(center_lat, center_lon, lat, lon)
        if dist > max_dist:
            max_dist = dist
    return max_dist


def get_hexagons_centers_in_polygon(polygon, resolution: int):
    """
    Возвращает все гексагоны resolution, центры которых внутри полигона.
    Работает через grid_disk + point_in_polygon (без polygon_to_cells).
    """
    # Находим центр полигона
    center_lat, center_lon = get_bbox_polygon_center(polygon)
    center_h3 = h3.latlng_to_cell(center_lat, center_lon, resolution)
    # Оцениваем радиус поиска в кольцах
    radius_m = get_bbox_polygon_radius_meters(polygon, center_lat, center_lon)
    cell_size = CELL_SIZES.get(resolution, DEFAULT_HEX_SIZE_M)
    k_rings = int(radius_m / cell_size) + K_RINGS_BUFFER
    # Собираем кандидатов
    candidates = h3.grid_disk(center_h3, k_rings)
    # Фильтруем по point_in_polygon
    result = set()
    for h3_idx in candidates:
        lat, lon = h3.cell_to_latlng(h3_idx)
        if point_in_polygon(lat, lon, polygon):
            result.add(h3_idx)
    return result


def get_hexagons_fully_inside_polygon(polygon, resolution: int):
    """
    Возвращает все гексагоны resolution, которые целиком внутри полигона.
    Проверяет все 6 вершин.
    """
    # Сначала находим кандидатов по центрам (быстрая фильтрация)
    candidates_by_center = get_hexagons_centers_in_polygon(polygon, resolution)
    # Проверяем каждый кандидат на полное вхождение
    result = []
    for h3_idx in candidates_by_center:
        if is_completely_inside_polygon(h3_idx, polygon):
            result.append(h3_idx)
    return set(result)
