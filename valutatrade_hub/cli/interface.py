"""Интерфейс командной строки"""

import argparse # Для парсинга команд
from typing import Dict, Any # Для аннотаций
from valutatrade_hub.core.usecases import (  # Импортируем функции команд из бизнесслогики
    register_user,
    login_user,
    show_portfolio,
    buy_currency,
    sell_currency,
    get_rate,
)

# Объявляем переменные для текущего пользователя
current_user_id: int = None
current_username: str = None

def parse_command_line(line: str) -> argparse.Namespace: # Функция парсинга команд
    """Парсит строку команды с помощью argparse"""
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


    # Разбиваем строку на аргументы
    args_list = line.strip().split()
    if not args_list:
        raise argparse.ArgumentError(None, "Пустая команда") # Если команда не введена, сообщаем об этом
    try:
        return parser.parse_args(args_list) # Запускаем парсер для аргументов команды
    except SystemExit:
        raise argparse.ArgumentError(None, "Ошибка в синтаксисе команды")


def main() -> None:
    """Точка входа CLI"""
    global current_user_id, current_username

    print("\nДобро пожаловать в ValutaTrade Hub!\n")
    print("\nВведите '-- help' или <команда> -- help, для справки.\n")
    print("\nВведите 'exit', чтобы выйти.\n")

    while True:
        try:
            line = input("\nВведите команду> ").strip()
        except (EOFError, KeyboardInterrupt): # Обрабатываем нажатие ctrl+C
            print("\nВыход.")
            break

        # Обработка встроенных команд
        if line == "exit":
            print("\nДо свидания!")
            break
        elif line == "logout": # Возможность сменить пользователя в процессе работы программы
            if current_user_id is None:
                print("\nВы не вошли в систему")
            else:
                current_user_id = None
                current_username = None
                print("\nВы вышли из системы")
            continue

        # Вызываем функцию парсинга команды
        try:
            args = parse_command_line(line)
        except argparse.ArgumentError as e:
           print(e)
           continue
        except Exception as e:
            print(e)
            continue

        # Выполняем команду
        if args.command == "register":    # Регистрация
            result = register_user(
                username=args.username,
                password=args.password,
            )
            if result["success"]:
                print(result["message"])
            else:
                print(result["message"])

        elif args.command == "login":     # Вход в систему
            result = login_user(
                username=args.username,
                password=args.password,
            )
            if result["success"]:
                current_user_id = result["user_id"]
                current_username = result["username"]
                print(result["message"])
            else:
                print(result["message"])

        elif args.command == "show-portfolio":    # Показать портфель
            if current_user_id is None:
                print("\nСначала войдите в систему")
            else:
                result = show_portfolio(
                    user_id=current_user_id,
                    base_currency=args.base,
                )
                if result["success"]:
                    print(result["message"])
                else:
                    print(result["message"])

        elif args.command == "buy":              # Купить валюту
            if current_user_id is None:
                print("\nСначала войдите в систему")
            else:
                result = buy_currency(
                    user_id=current_user_id,
                    currency_code=args.currency,
                    amount=args.amount,
                )
                if result["success"]:
                    print(result["message"])
                else:
                    print(result["message"])

        elif args.command == "sell":             # Продать валюту
            if current_user_id is None:
                print("\nСначала войдите в систему")
            else:
                result = sell_currency(
                    user_id=current_user_id,
                    currency_code=args.currency,
                    amount=args.amount,
                )
                if result["success"]:
                    print(result["message"])
                else:
                    print(result["message"])

        elif args.command == "get-rate":         # Получить курс
            result = get_rate(
                from_currency=getattr(args, "from"),
                to_currency=args.to,
            )
            if result["success"]:
                print(result["message"])
            else:
                print(result["message"])


if __name__ == "__main__":
    main()
