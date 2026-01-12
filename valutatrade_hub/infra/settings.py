"""
SettingsLoader - Singleton для загрузки конфигурации.
Из config.json.
"""

import json
from pathlib import Path
from typing import Any


class SettingsLoader:
    """
    Singleton для загрузки конфигурации.
    """
    
    _instance = None
    
    def __new__(cls) -> 'SettingsLoader':

        """
        Реализация Singleton через __new__.
        
        Выбран способ __new__ потому что:
        1. Проще и читабельнее, чем метаклассы
        2. Стандартный подход в Python
        3. Исключает создание дополнительных экземпляров при импортах
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = {}
            cls._instance._load_config()
        return cls._instance
    

    
    def _load_config(self) -> None:
        """Загружает конфигурацию из config.json."""
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / "config.json"
        
        if not config_path.exists():
            raise FileNotFoundError(
                f"Конфигурационный файл не найден: {config_path}\n"
                "Создайте config.json в корне проекта."
            )
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
        except json.JSONDecodeError:
            raise ValueError(f"Ошибка в формате config.json: {config_path}")
        except IOError:
            raise IOError(f"Не удалось прочитать config.json: {config_path}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Получает значение конфигурации по ключу."""
        return self._config.get(key, default)
    
    def reload(self) -> None:
        """Перезагружает конфигурацию."""
        self._load_config()