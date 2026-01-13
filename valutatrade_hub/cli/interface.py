"""
Интерфейс командной строки ValutaTrade Hub.
"""

import argparse # Для парсинга команд
import logging # Для логирования
from valutatrade_hub.core.usecases import ( # Команды CLI
    register_user,
    login_user,
    show_portfolio,
    buy_currency,
    sell_currency,
    get_rate,
)
from valutatrade_hub.parser_service.config import ParserConfig # Импорт классов для сервиса парсинга
from valutatrade_hub.parser_service.updater import RatesUpdater # Импорт классов для сервиса парсинга
from valutatrade_hub.parser_service.storage import RatesStorage # Импорт классов для сервиса парсинга


logger = logging.getLogger("valutatrade")


def parse_command_line(line: str) -> argparse.Namespace:
    """Парсит строку команды с помощью argparse."""
    parser = argparse.ArgumentParser(prog="valutatrade")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # register
    register_parser = subparsers.add_parser("register", help="Зарегистрироваться")
    register_parser.add_argument("--username", required=True, help="Имя пользователя")
    register_parser.add_argument("--password", required=True, help="Пароль")

    # login
    login_parser = subparsers.add_parser("login", help="Войти в систему")
    login_parser.add_argument("--username", required=True, help="Имя пользователя")
    login_parser.add_argument("--password", required=True, help="Пароль")

    # show-portfolio
    portfolio_parser = subparsers.add_parser("show-portfolio", help="Показать портфель")
    portfolio_parser.add_argument("--base", default="USD", help="Базовая валюта (по умолчанию USD)")

    # buy
    buy_parser = subparsers.add_parser("buy", help="Купить валюту")
    buy_parser.add_argument("--currency", required=True, help="Код валюты")
    buy_parser.add_argument("--amount", type=float, required=True, help="Количество валюты")

    # sell
    sell_parser = subparsers.add_parser("sell", help="Продать валюту")
    sell_parser.add_argument("--currency", required=True, help="Код валюты")
    sell_parser.add_argument("--amount", type=float, required=True, help="Количество валюты")

    # get-rate
    rate_parser = subparsers.add_parser("get-rate", help="Получить курс валюты")
    rate_parser.add_argument("--from", required=True, help="Исходная валюта (например, USD)")
    rate_parser.add_argument("--to", required=True, help="Целевая валюта (например, BTC)")

    # update-rates (сервис парсинга курсов)
    update_parser = subparsers.add_parser("update-rates", help="Обновить курсы валют из внешних API")
    update_parser.add_argument(
        "--source", 
        choices=["coingecko", "exchangerate"],
        help="Обновить только из указанного источника"
    )

    # show-rates (сервис парсинга курсов)
    show_rates_parser = subparsers.add_parser("show-rates", help="Показать курсы из локального кеша")
    show_rates_parser.add_argument(
        "--currency", 
        help="Показать курс только для указанной валюты"
    )
    show_rates_parser.add_argument(
        "--top", 
        type=int,
        help="Показать N самых дорогих криптовалют"
    )
    show_rates_parser.add_argument(
        "--base", 
        default="USD",
        help="Базовая валюта для отображения (по умолчанию USD)"
    )

    # Разбиваем строку на аргументы
    args_list = line.strip().split()
    if not args_list:
        raise argparse.ArgumentError(None, "Пустая команда")

    try:
        return parser.parse_args(args_list)
    except SystemExit:
        raise argparse.ArgumentError(None, "Ошибка в синтаксисе команды")


def run_cli() -> None:
    """Запускает CLI-интерфейс."""
    global current_user_id, current_username

    current_user_id = None
    current_username = None

    print("\nДобро пожаловать в ValutaTrade Hub!\n")
    print("\nВведите '-- help' или <команда> -- help, для справки.\n")
    print("\nВведите 'exit', чтобы выйти.\n")

    # Основной цикл
    while True:
        try:
            line = input("\nВведите команду> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nВыход.")
            break

        try:
            if line == "exit":
                print("\nДо свидания!")
                break
            elif line == "logout":
                if current_user_id is None:
                    print("\nВы не вошли в систему")
                else:
                    current_user_id = None
                    current_username = None
                    print("\nВы вышли из системы")
                continue

            try:
                args = parse_command_line(line)
            except argparse.ArgumentError as e:
                print(e)
                continue
            except Exception as e:
                print(e)
                continue

            # Выполняем команду
            if args.command == "register":
                result = register_user(
                    username=args.username,
                    password=args.password,
                )
                print(result["message"])

            elif args.command == "login":
                result = login_user(
                    username=args.username,
                    password=args.password,
                )
                if result["success"]:
                    current_user_id = result["user_id"]
                    current_username = result["username"]
                print(result["message"])

            elif args.command == "show-portfolio":
                if current_user_id is None:
                    print("\nСначала войдите в систему")
                else:
                    result = show_portfolio(
                        user_id=current_user_id,
                        base_currency=args.base,
                    )
                    print(result["message"])

            elif args.command == "buy":
                if current_user_id is None:
                    print("\nСначала войдите в систему")
                else:
                    result = buy_currency(
                        user_id=current_user_id,
                        currency_code=args.currency,
                        amount=args.amount,
                    )
                    print(result["message"])

            elif args.command == "sell":
                if current_user_id is None:
                    print("\nСначала войдите в систему")
                else:
                    result = sell_currency(
                        user_id=current_user_id,
                        currency_code=args.currency,
                        amount=args.amount,
                    )
                    print(result["message"])

            elif args.command == "get-rate":
                result = get_rate(
                    from_currency=getattr(args, "from"),
                    to_currency=args.to,
                )
                if result["success"]:
                    print(result["message"])
                else:
                    error_msg = result["message"]
                    if "Неизвестная валюта" in error_msg:
                        print(f"Ошибка валюты: {error_msg}")
                        print("   Проверьте правильность кодов валют.")
                    elif "Курсы устарели" in error_msg or "TTL" in error_msg:
                        print(f"Ошибка актуальности: {error_msg}")
                        print("   Попробуйте позже или обновите курсы.")
                    elif "не удалось получить курс" in error_msg or "недоступен" in error_msg:
                        print(f"Ошибка данных: {error_msg}")
                        print("Возможно, курс для этой пары не поддерживается.")
                    else:
                        print(error_msg)


            # Обработка update-rates
            elif args.command == "update-rates":
                try:
                    print("🔄 Запуск обновления курсов...")
                    
                    # Создаем конфигурацию и хранилище
                    config = ParserConfig()
                    storage = RatesStorage(config)
                    updater = RatesUpdater(config, storage)
                    
                    # Запускаем обновление (с опциональным источником)
                    source = getattr(args, "source", None)
                    result = updater.run_update(source=source)
                    
                    if result["success"]:
                        print(f"Обновление успешно!")
                        print(f"   Обновлено курсов: {result['rates_count']}")
                        print(f"   Время обновления: {result['last_refresh']}")
                        
                        if result.get("errors"):
                            print(f"   ⚠️  Были ошибки: {len(result['errors'])}")
                            for err in result["errors"]:
                                print(f"      - {err}")
                    else:
                        print("Обновление не удалось.")
                        
                except Exception as e:
                    print(f"Ошибка при обновлении курсов: {e}")
                    print("   Проверьте, установлен ли API-ключ:")
                    print("   export EXCHANGERATE_API_KEY='ваш_ключ'")

            # Обработка show-rates
            elif args.command == "show-rates":
                try:
                    config = ParserConfig()
                    storage = RatesStorage(config)
                    data = storage.load_current_rates()
                    
                    if not data or "pairs" not in data:
                        print("Локальный кеш курсов пуст.")
                        print("   Выполните 'update-rates', чтобы загрузить данные.")
                        continue
                    
                    pairs = data["pairs"]
                    last_refresh = data.get("last_refresh", "неизвестно")
                    
                    print(f"📊 Курсы из кеша (обновлено: {last_refresh}):")
                    
                    # Применяем фильтры
                    currency_filter = getattr(args, "currency", None)
                    top_filter = getattr(args, "top", None)
                    base_currency = getattr(args, "base", "USD")
                    
                    # Фильтруем по валюте и базе
                    filtered_pairs = {}
                    for pair, info in pairs.items():
                        # Проверяем валюту и базу
                        if currency_filter and currency_filter not in pair:
                            continue
                        if not pair.endswith(f"_{base_currency}"):
                            continue
                        filtered_pairs[pair] = info
                    
                    # Сортируем по курсу
                    sorted_pairs = sorted(
                        filtered_pairs.items(),
                        key=lambda x: x[1]["rate"],
                        reverse=True
                    )
                    
                    # Применяем ограничение по количеству
                    if top_filter and top_filter > 0:
                        sorted_pairs = sorted_pairs[:top_filter]
                    
                    # Выводим результат
                    if not sorted_pairs:
                        if currency_filter:
                            print(f"   Курс для '{currency_filter}' не найден в кеше.")
                        else:
                            print(f"   Нет курсов для базовой валюты '{base_currency}'.")
                    else:
                        for pair, info in sorted_pairs:
                            rate = info["rate"]
                            source = info.get("source", "unknown")
                            updated_at = info.get("updated_at", "неизвестно")
                            print(f"   - {pair}: {rate:.4f} ({source}, обновлено: {updated_at})")
                            
                except Exception as e:
                    print(f"Ошибка при чтении курсов: {e}")
                    
        except Exception as e:
                print(f"Ошибка выполнения команды: {e}")