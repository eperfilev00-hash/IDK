import logging
import sys
from pathlib import Path

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)


def setup_logging(level: str = "INFO"):
    """Настройка логирования для всего приложения."""
    
    # Формат логов: время | уровень | модуль | сообщение
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    handlers = [
        # Вывод в консоль
        logging.StreamHandler(sys.stdout),
        # Запись в файл всех логов
        logging.FileHandler(LOG_DIR / "app.log", encoding="utf-8"),
        # Отдельный файл для ошибок
        logging.FileHandler(LOG_DIR / "error.log", encoding="utf-8"),
    ]
    
    # Настраиваем обработчик ошибок отдельно
    error_handler = handlers[2]
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s",
        datefmt=date_format
    )
    error_handler.setFormatter(error_formatter)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    root_logger.handlers.clear()
    
    # Общий формат для консоли и файла
    formatter = logging.Formatter(log_format, datefmt=date_format)
    
    for handler in handlers[:2]:
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
    
    root_logger.addHandler(error_handler)
    
    logging.info("Логирование инициализировано, уровень: %s", level)