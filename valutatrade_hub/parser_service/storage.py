"""
Операции чтения/записи файлов с курсами валют.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List
from .config import ParserConfig

logger = logging.getLogger("valutatrade.parser")


class RatesStorage:
    """Управление хранением курсов валют."""

    def __init__(self, config: ParserConfig):
        self.config = config
        self.rates_file = Path(config.RATES_FILE_PATH)
        self.history_file = Path(config.HISTORY_FILE_PATH)

        # Создаем директории, если их нет
        self.rates_file.parent.mkdir(parents=True, exist_ok=True)
        self.history_file.parent.mkdir(parents=True, exist_ok=True)

    def save_current_rates(self, data: Dict[str, Any]) -> None:
        """
        Сохраняет текущие курсы в rates.json (перезаписывает файл).

        Args:
            data: Данные для сохранения в формате задания.
        """
        try:
            # Атомарная запись через временный файл
            temp_file = self.rates_file.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            temp_file.replace(self.rates_file)
            logger.info(f"Текущие курсы сохранены в {self.rates_file}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении текущих курсов: {e}")
            raise

    def save_to_history(self, rates: Dict[str, float], timestamp: str) -> None:
        """
        Добавляет записи в исторический журнал exchange_rates.json.

        Args:
            rates: Словарь с курсами валютных пар.
            timestamp: Временная метка обновления.
        """
        try:
            # Читаем существующую историю
            history = self._load_history()

            for pair, rate in rates.items():
                # Формируем уникальный ID
                from_curr, to_curr = pair.split("_")
                record_id = f"{from_curr}_{to_curr}_{timestamp.replace(':', '-').replace('+', '-')}"

                # Создаем запись
                record = {
                    "id": record_id,
                    "from_currency": from_curr,
                    "to_currency": to_curr,
                    "rate": rate,
                    "timestamp": timestamp,
                    "source": self._get_source_for_pair(pair),
                    "meta": {
                        "record_id": str(uuid.uuid4())[:8],
                        "status_code": 200,
                    }
                }

                history.append(record)

            # Сохраняем обновленную историю
            self._save_history(history)
            logger.debug(f"В историю добавлено {len(rates)} записей")

        except Exception as e:
            logger.error(f"Ошибка при сохранении в историю: {e}")
            raise

    def _load_history(self) -> List[Dict[str, Any]]:
        """Загружает исторические данные из файла."""
        if not self.history_file.exists():
            return []

        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            logger.warning(f"Файл {self.history_file} поврежден. Будет создан новый.")
            return []

    def _save_history(self, data: List[Dict[str, Any]]) -> None:
        """Сохраняет исторические данные в файл."""
        temp_file = self.history_file.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        temp_file.replace(self.history_file)

    def _get_source_for_pair(self, pair: str) -> str:
        """Определяет источник для валютной пары (упрощенная версия)."""
        currency = pair.split("_")[0]
        config = self.config

        if currency in config.CRYPTO_CURRENCIES:
            return "CoinGecko"
        elif currency in config.FIAT_CURRENCIES:
            return "ExchangeRate-API"
        return "unknown"

    def load_current_rates(self) -> Dict[str, Any]:
        """Загружает текущие курсы из rates.json."""
        if not self.rates_file.exists():
            return {}

        try:
            with open(self.rates_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"Не удалось загрузить текущие курсы: {e}")
            return {}