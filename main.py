"""
Точка входа в приложение ValutaTrade Hub.
"""

from valutatrade_hub.cli.interface import run_cli
from valutatrade_hub.infra.settings import SettingsLoader
from valutatrade_hub.logging_config import setup_logging


def main():
    # Загружаем настройки
    SettingsLoader()

    # Настраиваем логирование
    logger = setup_logging()
    logger.info("Запуск ValutaTrade Hub CLI")

    # Запускаем CLI
    run_cli()