from collections import defaultdict
import time
import sys
import json

from fastapi import FastAPI, Query, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse
from functools import lru_cache
import tempfile
import uvicorn

from constants import (
    CACHE_MAX_SIZE,
    MIN_RESOLUTION,
    MAX_RESOLUTION,
    DEFAULT_LIMIT,
    MAX_LIMIT,
    DEFAULT_BBOX_LIMIT,
    MAX_BBOX_LIMIT,
    MS_PER_SECOND,
    BYTES_PER_KB,
    KB_PER_MB,
)
from utils.kml_gen import generate_kml
from utils.logger import logger, timed_request
from services.h3_data import (
    get_dataset,
    get_parent_hex,
    median_floor,
    RESOLUTION,
    parse_border,
    get_hexagons_fully_inside_polygon,
)
import h3

app = FastAPI(title="H3 Dataset API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def polygon_to_cache_key(polygon):
    """
    Преобразует полигон в строку для использования в качестве ключа кэша.
    Используем JSON для надёжности.
    """
    return json.dumps(polygon, sort_keys=True)


@lru_cache(maxsize=CACHE_MAX_SIZE)
def get_cached_bbox_results(cache_key: str):
    """
    Кэширует результат вычисления гексагонов внутри полигона.
    cache_key — JSON-строка полигона.
    """
    # Восстанавливаем полигон из JSON
    polygon = json.loads(cache_key)
    # Преобразуем в кортежи (нужно для хэширования внутри функций)
    polygon = [tuple(p) for p in polygon]
    dataset = get_dataset()
    dataset_by_hex = {item[0]: item for item in dataset}
    # Получаем гексагоны, целиком внутри полигона
    hexes_fully_inside = get_hexagons_fully_inside_polygon(polygon, RESOLUTION)
    # Фильтруем по датасету
    result = []
    for h3_idx in hexes_fully_inside:
        if h3_idx in dataset_by_hex:
            result.append(dataset_by_hex[h3_idx])
    logger.info(f"Кэш для /bbox: вычислено {len(result)} гексагонов")
    return result


@app.get("/hex")
@timed_request
async def endpoint_hex(hex: str = Query(..., description="H3 индекс гексагона")):
    """
    Возвращает элементы датасета, входящие в заданный гексагон.
    """
    if not h3.is_valid_cell(hex):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid H3 index")
    dataset = get_dataset()
    result = []
    requested_res = h3.get_resolution(hex)
    for h3_idx, level, cell_id in dataset:
        if requested_res == RESOLUTION:
            if h3_idx == hex:
                result.append([h3_idx, level, cell_id])
        elif requested_res < RESOLUTION:
            parent = h3.cell_to_parent(h3_idx, requested_res)
            if parent == hex:
                result.append([h3_idx, level, cell_id])
    return JSONResponse(content=result)


@app.get("/avg")
@timed_request
async def endpoint_avg(
    resolution: int = Query(
        ..., ge=MIN_RESOLUTION, le=MAX_RESOLUTION, description="Целевое разрешение"
    ),
    limit: int = Query(
        DEFAULT_LIMIT, ge=1, le=MAX_LIMIT, description="Количество результатов на странице"
    ),
    offset: int = Query(0, ge=0, description="Смещение (пагинация)"),
):
    """
    Возвращает гексагоны заданного разрешения с медианным значением level,
    сгруппированным по cell_id.
    """
    dataset = get_dataset()
    groups = defaultdict(list)
    for h3_idx, level, cell_id in dataset:
        try:
            parent = get_parent_hex(h3_idx, resolution)
            groups[(parent, cell_id)].append(level)
        except Exception as e:
            logger.error(e)
            continue
    full_result = [
        [parent, median_floor(levels), cell_id] for (parent, cell_id), levels in groups.items()
    ]
    total = len(full_result)
    paginated_result = full_result[offset : offset + limit]
    return JSONResponse(
        content={
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_next": offset + limit < total,
            "data": paginated_result,
        }
    )


@app.get("/bbox")
@timed_request
async def endpoint_bbox(
    border: str = Query(..., description="lat/lon,lat/lon,..."),
    limit: int = Query(
        DEFAULT_BBOX_LIMIT,
        ge=1,
        le=MAX_BBOX_LIMIT,
        description="Количество результатов на странице",
    ),
    offset: int = Query(0, ge=0, description="Смещение (пагинация)"),
):
    """
    Возвращает гексагоны из датасета, которые целиком помещаются внутри заданного полигона.
    Результат кэшируется.
    Пример: 56.1/37.9,56.1/38.1,55.9/38.1,55.9/37.9,56.1/37.9
    """
    try:
        polygon = parse_border(border)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))
    # Создаём ключ для кэша (JSON)
    cache_key = polygon_to_cache_key(polygon)
    # Получаем из кэша или вычисляем
    full_result = get_cached_bbox_results(cache_key)
    total = len(full_result)
    paginated_result = full_result[offset : offset + limit]
    logger.info(f"/bbox: {total} гексагонов, возвращено {len(paginated_result)}")
    return JSONResponse(
        content={
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_next": offset + limit < total,
            "data": paginated_result,
        }
    )


@app.get("/bbox_kml")
@timed_request
async def endpoint_bbox_kml(border: str = Query(..., description="lat/lon,lat/lon,...")):
    """
    Возвращает KML файл с гексагонами внутри полигона.
    Пример: 56.01/37.99,56.01/38.00,55.99/38.00,55.99/37.99,56.01/37.99
    """
    try:
        polygon = parse_border(border)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))
    cache_key = polygon_to_cache_key(polygon)
    result_data = get_cached_bbox_results(cache_key)
    logger.info(f"/bbox_kml: {len(result_data)} гексагонов")
    kml_content = generate_kml(result_data)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".kml", delete=False) as f:
        f.write(kml_content)
        temp_path = f.name
    return FileResponse(
        temp_path, media_type="application/vnd.google-earth.kml+xml", filename="hexagons.kml"
    )


@app.get("/avg_benchmark")
@timed_request
async def endpoint_avg_benchmark(resolution: int = Query(..., ge=0, le=12)):
    """
    Диагностический эндпоинт.
    """
    dataset = get_dataset()
    start_time = time.perf_counter()
    groups = defaultdict(list)
    for h3_idx, level, cell_id in dataset:
        try:
            parent = get_parent_hex(h3_idx, resolution)
            groups[(parent, cell_id)].append(level)
        except Exception as e:
            logger.error(e)
            continue
    group_time = (time.perf_counter() - start_time) * MS_PER_SECOND
    start_median = time.perf_counter()
    result = []
    for (parent, cell_id), levels in groups.items():
        result.append([parent, median_floor(levels), cell_id])
    median_time = (time.perf_counter() - start_median) * MS_PER_SECOND
    approx_json_size_mb = sys.getsizeof(str(result)) / BYTES_PER_KB / KB_PER_MB
    return {
        "resolution": resolution,
        "total_records_in_dataset": len(dataset),
        "number_of_groups": len(groups),
        "result_rows": len(result),
        "time_grouping_ms": round(group_time, 2),
        "time_median_calc_ms": round(median_time, 2),
        "total_time_ms": round(group_time + median_time, 2),
        "approx_json_size_mb": round(approx_json_size_mb, 2),
        "note": "Данные не возвращены, только метрики",
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8888)
