"""
Настройка логирования для ValutaTrade Hub.
"""

import logging
import logging.handlers
from pathlib import Path
from valutatrade_hub.infra.settings import SettingsLoader


def setup_logging():
    """Настраивает логирование на основе конфигурации."""
    settings = SettingsLoader()
    log_dir = Path(settings.get("log_dir", "./logs"))
    log_file = log_dir / "actions.log"
    
    # Создаём директорию логов если нет
    log_dir.mkdir(exist_ok=True, parents=True)
    
    # Формат логов
    log_format = settings.get("log_format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Основной логгер
    logger = logging.getLogger("valutatrade")
    logger.setLevel(logging.INFO)
    
    # Убираем дублирование логов
    logger.propagate = False
    
    # Если обработчиков ещё нет
    if not logger.handlers:
        # Файловый обработчик с ротацией
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=10 * 1024 * 1024,  
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(log_format, datefmt=date_format)
        file_handler.setFormatter(file_formatter)
        
        # Консольный обработчик
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)  # Только ошибки в консоль
        console_formatter = logging.Formatter('%(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        
        # Добавляем обработчики
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger


# Автоматическая настройка при импорте
logger = setup_logging()