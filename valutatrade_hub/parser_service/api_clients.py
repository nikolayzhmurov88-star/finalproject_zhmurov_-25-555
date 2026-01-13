"""
Клиенты для работы с внешними API (CoinGecko, ExchangeRate-API).
"""

import requests # Для HTTPS запросов
import logging # Для логирования
from abc import ABC, abstractmethod # Для абстрактных классов
from typing import Dict, Any # Аннотации
from valutatrade_hub.core.exceptions import ApiRequestError # Исключение
from .config import ParserConfig # Конфигурация парсера

logger = logging.getLogger("valutatrade.parser")


class BaseApiClient(ABC):
    """Абстрактный базовый класс для API-клиентов."""

    @abstractmethod
    def fetch_rates(self) -> Dict[str, float]:
        """
        Получает актуальные курсы валют от API.

        Returns:
            Словарь вида {"BTC_USD": 59337.21, "EUR_USD": 0.927, ...}

        Raises:
            ApiRequestError: при ошибке сети или невалидном ответе API.
        """
        pass


class CoinGeckoClient(BaseApiClient):
    """Клиент для CoinGecko API (криптовалюты)."""

    def __init__(self, config: ParserConfig):
        self.config = config
    
    def fetch_rates(self) -> Dict[str, float]:
        """Получает курсы криптовалют к USD."""
        try:
            # Формируем списки ID и валют
            crypto_ids = [
                self.config.CRYPTO_ID_MAP[code]
                for code in self.config.CRYPTO_CURRENCIES
                if code in self.config.CRYPTO_ID_MAP
            ]
            if not crypto_ids:
                logger.warning("Нет криптовалют для запроса к CoinGecko.")
                return {}

            ids_param = ",".join(crypto_ids)
            url = f"{self.config.COINGECKO_URL}?ids={ids_param}&vs_currencies=usd"

            logger.debug(f"Запрос к CoinGecko: {url}")
            response = requests.get(url, timeout=self.config.REQUEST_TIMEOUT)
            response.raise_for_status() 

            data = response.json()

            # Преобразуем ответ в единый формат
            result = {}
            for crypto_code, gecko_id in self.config.CRYPTO_ID_MAP.items():
                if gecko_id in data and "usd" in data[gecko_id]:
                    rate = data[gecko_id]["usd"]
                    pair = f"{crypto_code}_{self.config.BASE_FIAT_CURRENCY}"
                    result[pair] = rate
                    logger.debug(f"Получен курс {pair}: {rate}")

            logger.info(f"CoinGecko: успешно получено {len(result)} курсов.")
            return result

        except requests.exceptions.RequestException as e:
            error_msg = f"Ошибка сети при запросе к CoinGecko: {e}"
            logger.error(error_msg)
            raise ApiRequestError(error_msg)
        except (KeyError, ValueError) as e:
            error_msg = f"Неверный формат ответа от CoinGecko: {e}"
            logger.error(error_msg)
            raise ApiRequestError(error_msg)

  
class ExchangeRateApiClient(BaseApiClient):
    """Клиент для ExchangeRate-API (фиатные валюты)."""

    def __init__(self, config: ParserConfig):
        self.config = config

    def fetch_rates(self) -> Dict[str, float]:
        """Получает курсы фиатных валют к USD."""
        try:
            # Формируем полный URL из базового URL, API ключа и эндпоинта
            url = f"{self.config.EXCHANGERATE_API_URL}/{self.config.EXCHANGERATE_API_KEY}/latest/USD"
            logger.debug(f"Запрос к ExchangeRate-API: {url}")
            response = requests.get(url, timeout=self.config.REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            # Проверяем успешность ответа API
            if data.get("result") != "success":
                error_msg = f"API вернуло ошибку: {data.get('error-type', 'unknown')}"
                logger.error(error_msg)
                raise ApiRequestError(error_msg)

            # Получаем курсы
            rates = data.get("conversion_rates", {})
            
            result = {}
            for currency in self.config.FIAT_CURRENCIES:
                if currency in rates:
                    rate = float(rates[currency])
                    pair = f"{currency}_{self.config.BASE_FIAT_CURRENCY}"
                    result[pair] = rate
                    logger.debug(f"Получен курс {pair}: {rate}")
                else:
                    logger.warning(f"Валюта {currency} не найдена в ответе API")

            logger.info(f"ExchangeRate-API: успешно получено {len(result)} курсов.")
            return result

        except requests.exceptions.RequestException as e:
            error_msg = f"Ошибка сети при запросе к ExchangeRate-API: {e}"
            logger.error(error_msg)
            raise ApiRequestError(error_msg)
        except (KeyError, ValueError) as e:
            error_msg = f"Неверный формат ответа от ExchangeRate-API: {e}"
            logger.error(error_msg)
            raise ApiRequestError(error_msg)