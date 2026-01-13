"""
Точка входа в приложение ValutaTrade Hub.
"""

from valutatrade_hub.cli.interface import run_cli
from valutatrade_hub.infra.settings import SettingsLoader
from valutatrade_hub.logging_config import setup_logging
from valutatrade_hub.parser_service.scheduler import RateUpdateScheduler
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.parser_service.storage import RatesStorage
from valutatrade_hub.parser_service.updater import RatesUpdater


def main():
    # Загружаем настройки
    SettingsLoader()

    # Настраиваем логирование
    logger = setup_logging()
    logger.info("\nЗапуск ValutaTrade Hub CLI")

    # Обновляем курсы при запуске
    try:
        print("\nОбновление курсов ...")
        
        # Создаем объекты для обновления
        parser_config = ParserConfig()
        storage = RatesStorage(parser_config)
        updater = RatesUpdater(parser_config, storage)
        
        # Запускаем обновление
        result = updater.run_update()
        
        if result["success"]:
            print(f"Курсы обновлены: {result['rates_count']} курсов")
            print(f"Последнее обновление: {result['last_refresh']}")
        else:
            print("Не удалось обновить курсы")
            if result.get("errors"):
                for error in result["errors"]:
                    print(f"   - {error}")
    except Exception as e:
        print(f"Ошибка при обновлении курсов: {e}")

    # Запускаем планировщик
    try:
        parser_config = ParserConfig()
        scheduler = RateUpdateScheduler(parser_config, interval_minutes=60)
        scheduler.start()
        print("\nПланировщик запущен (обновление каждые 60 минут)")
    except Exception as e:
        print(f"Не удалось запустить планировщик: {e}")

    # Запускаем CLI
    run_cli()


if __name__ == "__main__":
    main()