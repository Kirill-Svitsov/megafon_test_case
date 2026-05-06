import logging
import sys
import time
from functools import wraps

from constants import LEVEL_COLORS, RESET, MS_PER_SECOND


class ColoredFormatter(logging.Formatter):
    def format(self, record):
        color = LEVEL_COLORS.get(record.levelname, RESET)
        record.levelname = f"{color}{record.levelname}{RESET}"
        return super().format(record)


def setup_logger():
    LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(message)s"
    DATE_FORMAT = "%H:%M:%S"
    logger = logging.getLogger("h3_api")
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(ColoredFormatter(LOG_FORMAT, DATE_FORMAT))
        logger.addHandler(handler)
    return logger


logger = setup_logger()


def timed_request(func):
    """
    Декоратор для замера времени выполнения запроса.
    Логирует время и добавляет поле duration_ms в ответ.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            duration_ms = (time.perf_counter() - start_time) * MS_PER_SECOND
            logger.info(f"{func.__name__} | {duration_ms:.2f}ms")
            # Если результат - словарь или список, добавляем время
            if isinstance(result, dict):
                result["_duration_ms"] = round(duration_ms, 2)
            elif isinstance(result, list):
                result = {"data": result, "_duration_ms": round(duration_ms, 2)}
            return result
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * MS_PER_SECOND
            logger.error(f"{func.__name__} | failed in {duration_ms:.2f}ms | {str(e)}")
            raise

    return wrapper
