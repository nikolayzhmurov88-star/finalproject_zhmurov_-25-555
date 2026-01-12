"""
Конфигурация для Parser Service.
"""

import os
from dataclasses import dataclass
from typing import Tuple, Dict


@dataclass
class ParserConfig:
    """
    Конфигурация парсера. API-ключ загружается из переменной окружения
    """
    
    # API Ключи
    # Приоритет: 1. Переменная окружения, 2. Хардкод для отладки
    _DEBUG_API_KEY = ""  # !!!!УДАЛИТЬ ПЕРЕД КОММИОМ
    
    EXCHANGERATE_API_KEY: str = os.getenv("EXCHANGERATE_API_KEY", _DEBUG_API_KEY)

    # URL-адреса запросов
    # URL для получения цен криптовалют
    COINGECKO_API_URL: str = "https://api.coingecko.com/api/v3/simple/price"
    
    # Полный URL для получения курсов фиатных валют
    @property
    def EXCHANGERATE_API_URL(self) -> str:
        """Полный URL для запроса курсов валют."""
        return f"https://v6.exchangerate-api.com/v6/{self.EXCHANGERATE_API_KEY}/latest/USD"

    # Списки отслеживаемых валют
    BASE_FIAT_CURRENCY: str = "USD"
    FIAT_CURRENCIES: Tuple[str, ...] = ("EUR", "GBP", "RUB")
    CRYPTO_CURRENCIES: Tuple[str, ...] = ("BTC", "ETH", "SOL")
    
    CRYPTO_ID_MAP: Dict[str, str] = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SOL": "solana",
    }

    # Сетевые параметры
    REQUEST_TIMEOUT: int = 10

    # Пути к файлам
    RATES_FILE_PATH: str = "data/rates.json"
    HISTORY_FILE_PATH: str = "data/exchange_rates.json"

    def __post_init__(self):
        """Проверка обязательных настроек после инициализации."""
        if not self.EXCHANGERATE_API_KEY:
            raise ValueError(
                "API-ключ для ExchangeRate-API не найден. "
                "Установите переменную окружения 'EXCHANGERATE_API_KEY'."
            )