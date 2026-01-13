"""
Координатор обновления курсов валют.
"""

import logging # Для логирования
from typing import Dict, Any # Для логирование
from datetime import datetime, timezone # Для времени
from .config import ParserConfig # Конфигурация парсера
from .api_clients import CoinGeckoClient, ExchangeRateApiClient # Классы API клиентов
from .storage import RatesStorage # Работа с JSON
from valutatrade_hub.core.exceptions import ApiRequestError # Исключения

logger = logging.getLogger("valutatrade.parser")


class RatesUpdater:
    """Координирует процесс обновления курсов."""

    def __init__(self, config: ParserConfig, storage: RatesStorage):
        self.config = config
        self.storage = storage
        self.clients = {
            "coingecko": CoinGeckoClient(config),
            "exchangerate": ExchangeRateApiClient(config),
        }

    def run_update(self, source: str = None) -> Dict[str, Any]:
        """
        Запускает обновление курсов.

        Args:
            source: Если указан ('coingecko' или 'exchangerate'),
                    обновляет только из этого источника. По умолчанию - все.

        Returns:
            Словарь с результатами обновления.

        Raises:
            ApiRequestError: если произошла критическая ошибка API.
        """
        logger.info("Запуск обновления курсов...")
        if source:
            logger.info(f"Обновление только из источника: {source}")

        all_rates = {}
        errors = []
        timestamp = datetime.now(timezone.utc).isoformat()

        # Определяем, какие клиенты нужно опросить
        clients_to_run = {}
        if source:
            if source in self.clients:
                clients_to_run[source] = self.clients[source]
            else:
                logger.error(f"Неизвестный источник: {source}")
                return {"success": False, "errors": [f"Неизвестный источник: {source}"]}
        else:
            clients_to_run = self.clients

        # Опрашиваем клиентов
        for client_name, client in clients_to_run.items():
            try:
                logger.info(f"Получение данных от {client_name}...")
                rates = client.fetch_rates()
                all_rates.update(rates)
                logger.info(f"{client_name}: OK ({len(rates)} курсов)")
            except ApiRequestError as e:
                error_msg = f"Ошибка при получении данных от {client_name}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
                # Продолжаем работу с другими источниками

        if not all_rates and errors:
            # Если ни один источник не сработал
            raise ApiRequestError(f"Все источники данных недоступны. Ошибки: {errors}")

        # Формируем итоговый объект для сохранения
        result_data = {
            "pairs": {},
            "last_refresh": timestamp,
            "meta": {
                "sources_used": list(clients_to_run.keys()),
                "errors_encountered": errors if errors else None,
            }
        }

        for pair, rate in all_rates.items():
            result_data["pairs"][pair] = {
                "rate": rate,
                "updated_at": timestamp,
                "source": self._get_source_for_pair(pair)
            }

        # Сохраняем данные
        try:
            self.storage.save_current_rates(result_data)
            self.storage.save_to_history(all_rates, timestamp)
        except Exception as e:
            error_msg = f"Ошибка при сохранении данных: {e}"
            logger.error(error_msg)
            raise ApiRequestError(error_msg)

        logger.info(f"Обновление завершено. Сохранено {len(all_rates)} курсов.")
        return {
            "success": True,
            "rates_count": len(all_rates),
            "last_refresh": timestamp,
            "errors": errors if errors else None,
        }

    def _get_source_for_pair(self, pair: str) -> str:
        """Определяет источник данных для валютной пары."""
        currency = pair.split("_")[0]
        if currency in self.config.CRYPTO_CURRENCIES:
            return "CoinGecko"
        elif currency in self.config.FIAT_CURRENCIES:
            return "ExchangeRate-API"
        return "unknown"