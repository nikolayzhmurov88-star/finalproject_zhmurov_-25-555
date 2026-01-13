"""
Планировщик периодического обновления курсов.
"""

import logging
import threading
import time
from typing import Optional
from .config import ParserConfig
from .updater import RatesUpdater
from .storage import RatesStorage

logger = logging.getLogger("valutatrade.parser")


class RateUpdateScheduler:
    """Планировщик для автоматического обновления курсов."""

    def __init__(self, config: ParserConfig, interval_minutes: int = 60):
        self.config = config
        self.interval = interval_minutes * 60  # в секундах
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Запускает фоновый поток для периодического обновления."""
        if self._thread and self._thread.is_alive():
            logger.warning("Планировщик уже запущен.")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info(f"Планировщик запущен. Интервал: {self.interval//60} минут.")

    def stop(self) -> None:
        """Останавливает планировщик."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
            logger.info("Планировщик остановлен.")

    def _run(self) -> None:
        """Основной цикл планировщика."""
        storage = RatesStorage(self.config)
        updater = RatesUpdater(self.config, storage)

        while not self._stop_event.is_set():
            try:
                logger.info("Запланированное обновление курсов...")
                result = updater.run_update()
                if result["success"]:
                    logger.info(f"Обновлено {result['rates_count']} курсов.")
                else:
                    logger.warning("Обновление завершилось с ошибками.")
            except Exception as e:
                logger.error(f"Ошибка в планировщике: {e}")

            # Ожидаем указанный интервал или сигнал остановки
            self._stop_event.wait(self.interval)

    def run_once(self) -> None:
        """Выполняет одно обновление вне расписания."""
        storage = RatesStorage(self.config)
        updater = RatesUpdater(self.config, storage)
        updater.run_update()