"""Бизнес-логика"""

import json # Для работы с JSON
from typing import Dict, Any # для аннотаций
from valutatrade_hub.infra.settings import SettingsLoader # Синглтон
import valutatrade_hub.constants as const # Импорт констант
from valutatrade_hub.core.models import User, Portfolio, Wallet # Импорт основных классов программы
from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.exceptions import ( # Импортируем исключения
    InsufficientFundsError,
    CurrencyNotFoundError,
    ApiRequestError)
from valutatrade_hub.decorators import log_action # Импортируем декоратор для логирования
import logging # Библиотека для логирования
import time # Время


# Вспомогательные функции для работы с JSON
def load_json(path: const.Path) -> Dict[str, Any]:
    """Загружает JSON из файла, возвращает пустой словарь, если файла нет."""
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: const.Path, data: Dict[str, Any]) -> None:
    """Сохраняет словарь в JSON-файл."""
    path.parent.mkdir(exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Функция для безопасной записи
def safe_json_operation(file_path: const.Path, operation_func) -> Any:
    """Безопасная операция чтение→модификация→запись."""
    try:
        # Чтение
        if not file_path.exists():
            data = {}
        else:
            with file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        
        # Модификация
        new_data = operation_func(data)
        
        # Запись
        file_path.parent.mkdir(exist_ok=True, parents=True)
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(new_data, f, ensure_ascii=False, indent=2)
        
        return new_data
        
    except Exception as e:
        logger = logging.getLogger("valutatrade")
        logger.error(f"Ошибка при работе с {file_path}: {e}")
        raise



# 1. Команда регистрации
@log_action(action="REGISTER", verbose=True) 
def register_user(username: str, password: str) -> Dict[str, Any]:
    """Регистрирует нового пользователя."""
    try:
        users_data = load_json(const.USERS_FILE)
        users = users_data.get("users", [])

        # Проверка: username не пустой и уникален
        username = username.strip()

        for user in users:
            if user["username"] == username:
                return {"success": False, "message": f"\nИмя пользователя '{username}' уже занято"}

        # Генерируем user_id
        user_id = 1
        if users:
            user_id = max(u["user_id"] for u in users) + 1

        # Создаём User 
        user = User(
            user_id=user_id,
            username=username,
            password=password,
        )

        # Сохраняем пользователя
        users.append(user.to_dict())
        save_json(const.USERS_FILE, {"users": users})

        # Создаём портфель
        portfolio = Portfolio(user_id = user_id, wallets={})

        # Добавляем USD-кошелёк и пополняем на 100 000
        portfolio.add_currency("USD")
        wallet_usd = portfolio.get_wallet("USD")
        wallet_usd.deposit(100000.0)

        # Сохраняем портфель в JSON
        portfolios_data = load_json(const.PORTFOLIOS_FILE)
        portfolios = portfolios_data.get("portfolios", [])
        portfolios.append(portfolio.to_dict())
        save_json(const.PORTFOLIOS_FILE, {"portfolios": portfolios})


        return {
            "success": True,
            "message": f"\nПользователь '{username}' зарегистрирован (id={user_id}). Войдите: login --username {username} --password ****"
        }
    
    except ValueError as e:
        # Ловим ValueError 
        return {"success": False, "message": str(e)}

    except Exception as e:
        logger = logging.getLogger("valutatrade")
        logger.error(f"Неожиданная ошибка при регистрации: {e}")
        return {"success": False, "message": "\nОшибка при регистрации"}

# 2. Команда входа в систему
@log_action(action="LOGIN", verbose=True) 
def login_user(username: str, password: str) -> Dict[str, Any]:
    """Входит в систему под пользователем"""

    username = username.strip()
    users_data = load_json(const.USERS_FILE)
    users = users_data.get("users", [])

    user_data = None
    for u in users:
        if u["username"] == username:
            user_data = u
            break

    if user_data is None:
        return {"success": False, "message": f"\nПользователь '{username}' не найден"}

    # Восстанавливаем User из словаря
    user = User.from_dict(user_data)

    if not user.verify_password(password):
        return {"success": False, "message": "\nНеверный пароль"}

    return {
        "success": True,
        "user_id": user.user_id,
        "username": user.username,
        "message": f"\nВы вошли как: {username}"
    }


# 3. Команда показа портфеля
def show_portfolio(user_id: int, base_currency: str = "USD") -> Dict[str, Any]:
    """Показывает портфель пользователя"""
    portfolios_data = load_json(const.PORTFOLIOS_FILE)
    portfolios = portfolios_data.get("portfolios", [])

    # Ищем портфель по user_id
    portfolio_data = None
    for p in portfolios:
        if p["user_id"] == user_id:
            portfolio_data = p
            break

    if portfolio_data is None:
        return {"success": False, "message": "Портфель не найден"}

    # Создаём объект Portfolio
    portfolio = Portfolio.from_dict(portfolio_data)

    # Формируем вывод
    lines = []
    lines.append(f"\nПортфель пользователя (база: {base_currency}):")

    if not portfolio_data["wallets"]:
        lines.append("\nУ вас пока нет кошельков.")
    else:
        # Показываем каждый кошелёк
        for currency, wallet_info in portfolio_data["wallets"].items():
            balance = wallet_info["balance"]
            lines.append(f"- {currency}: {balance:.4f}")

        # Итоговая стоимость — считает get_total_value
        total_value = portfolio.get_total_value(base_currency=base_currency)
        lines.append("---------------------------------")
        lines.append(f"\nИтого: {total_value:,.2f} {base_currency}")

    return {
        "success": True,
        "message": "\n".join(lines)
    }
    

# 4. Команда купить валюту
@log_action(action="BUY", verbose=True) # Декоратор для логирования
def buy_currency(user_id: int, currency_code: str, amount: float) -> Dict[str, Any]:
    """Покупает валюту"""
    if not currency_code or not currency_code.strip():
        return {"success": False, "message": "Код валюты не может быть пустым"}
    currency_code = currency_code.strip().upper()

    if not isinstance(amount, (int, float)) or amount <= 0:
        return {"success": False, "message": "'amount' должен быть положительным числом"}
    
 
    # Проверяем существование валюты
    try:
        get_currency(currency_code)
    except CurrencyNotFoundError as e:
        return {"success": False, "message": str(e)}

    # Загружаем портфель
    portfolios_data = load_json(const.PORTFOLIOS_FILE)
    portfolios = portfolios_data.get("portfolios", [])

    portfolio_data = None
    for p in portfolios:
        if p["user_id"] == user_id:
            portfolio_data = p
            break

    if portfolio_data is None:
        return {"success": False, "message": "Портфель не найден"}

    # Создаём объект Portfolio
    portfolio = Portfolio.from_dict(portfolio_data)

    # Получаем курс из rates.json
    rates_data = load_json(const.RATES_FILE)
    if not isinstance(rates_data, dict):
        return {"success": False, "message": str(ApiRequestError("файл rates.json повреждён или пустой"))}

    # Ищем пару currency_code → USD
    pair = f"{currency_code}_USD"
    rate_info = rates_data.get(pair)

    if rate_info is None:
        return {"success": False, "message": str(ApiRequestError(f"не удалось получить курс для {currency_code}→USD"))}

    if not isinstance(rate_info, dict) or "rate" not in rate_info:
        return {"success": False, "message": str(ApiRequestError(f"неверный формат курса для {currency_code}→USD"))}
    
    rate = rate_info["rate"]
    cost_usd = amount * rate

    # Работаем с кошельками через методы Portfolio
    try:
        # Получаем USD-кошелёк
        usd_wallet = portfolio.get_wallet("USD")
        if usd_wallet.balance < cost_usd:
            return {
                "success": False,
                "message": str(InsufficientFundsError(
                    available=usd_wallet.balance,
                    required=cost_usd,
                    code="USD"
                ))
            }

        # Добавляем валюту, если её ещё нет
        if currency_code not in portfolio._wallets:
            portfolio.add_currency(currency_code)

        # Получаем кошелёк валюты
        target_wallet: Wallet = portfolio.get_wallet(currency_code)
        old_balance: Wallet = target_wallet.balance

        # Списываем USD и пополняем валюту
        usd_wallet.withdraw(cost_usd)
        target_wallet.deposit(amount)

        # Сохраняем обновлённый портфель

        def update_portfolio(data):
            portfolios = data.get("portfolios", [])
            for i, p in enumerate(portfolios):
                if p["user_id"] == user_id:
                    # Обновляем только нужный портфель
                    p["wallets"] = {k: {"balance": v.balance} for k, v in portfolio._wallets.items()}
                    portfolios[i] = p
                    break
            data["portfolios"] = portfolios
            return data
        
        safe_json_operation(const.PORTFOLIOS_FILE, update_portfolio)

        # Формируем сообщение
        lines = []
        lines.append(f"\nПокупка выполнена: {amount:.4f} {currency_code} по курсу {rate:.2f} USD/{currency_code}")
        lines.append("\nИзменения в портфеле:")
        lines.append(f"\n- {currency_code}: было {old_balance:.4f} → стало {target_wallet.balance:.4f}")
        lines.append(f"\nОценочная стоимость покупки: {cost_usd:.2f} USD")

        return {"success": True, "message": "\n".join(lines)}

    except (KeyError, ValueError) as e:
        return {"success": False, "message": str(e)}


# 5. Команда на продажу валюты
@log_action(action="SELL", verbose=True) # Декоратор для логирования
def sell_currency(user_id: int, currency_code: str, amount: float) -> Dict[str, Any]:
    """Продаёт валюту"""
    if not currency_code or not currency_code.strip():
        return {"success": False, "message": "Код валюты не может быть пустым"}
    currency_code = currency_code.strip().upper()

    if not isinstance(amount, (int, float)) or amount <= 0:
        return {"success": False, "message": "'amount' должен быть положительным числом"}
    
    # Валидация валюты
    try:
        get_currency(currency_code)  
    except CurrencyNotFoundError as e:
        return {"success": False, "message": str(e)}

    # Загружаем портфель
    portfolios_data = load_json(const.PORTFOLIOS_FILE)
    portfolios = portfolios_data.get("portfolios", [])

    portfolio_data = None
    for p in portfolios:
        if p["user_id"] == user_id:
            portfolio_data = p
            break

    if portfolio_data is None:
        return {"success": False, "message": "\nПортфель не найден"}

    # Создаём объект Portfolio
    portfolio = Portfolio.from_dict(portfolio_data)

    # Проверяем, есть ли такая валюта
    if currency_code not in portfolio._wallets:
        return {"success": False, "message": f"\nВалюта {currency_code} не найдена в портфеле"}

    # Получаем кошелёк
    wallet: Wallet = portfolio.get_wallet(currency_code)
    if wallet.balance < amount:
        return {
        "success": False,
        "message": str(InsufficientFundsError(
            available=wallet.balance,
            required=amount,
            code=currency_code
            ))
        }

    # Получаем курс из rates.json    
    rates_data = load_json(const.RATES_FILE)
    if not isinstance(rates_data, dict):
        return {"success": False, "message": str(ApiRequestError("файл rates.json повреждён или пустой"))}

    # Ищем пару currency_code → USD
    pair = f"{currency_code}_USD"
    rate_info = rates_data.get(pair)

    if rate_info is None:
        return {"success": False, "message": str(ApiRequestError(f"не удалось получить курс для {currency_code}→USD"))}

    if not isinstance(rate_info, dict) or "rate" not in rate_info:
        return {"success": False, "message": str(ApiRequestError(f"неверный формат курса для {currency_code}→USD"))}

    rate = rate_info["rate"]
    revenue_usd = amount * rate

    # Сохраняем старый баланс
    old_balance = wallet.balance

    # Списываем валюту и пополняем USD
    wallet.withdraw(amount)
    usd_wallet: Wallet = portfolio.get_wallet("USD")
    usd_wallet.deposit(revenue_usd)


    # Сохраняем обновлённый портфель
    def update_portfolio(data):
        portfolios = data.get("portfolios", [])
        for i, p in enumerate(portfolios):
            if p["user_id"] == user_id:
                # Обновляем только нужный портфель
                p["wallets"] = {k: {"balance": v.balance} for k, v in portfolio._wallets.items()}
                portfolios[i] = p
                break
        data["portfolios"] = portfolios
        return data
    
    try:
        # Используем безопасную операцию
        data = load_json(const.PORTFOLIOS_FILE)
        new_data = update_portfolio(data)
        save_json(const.PORTFOLIOS_FILE, new_data)
    except Exception as e:
        logger = logging.getLogger("valutatrade")
        logger.error(f"Ошибка сохранения портфеля: {e}")
        return {"success": False, "message": "Ошибка при сохранении данных"}


    # Формируем сообщение
    lines = []
    lines.append(f"\nПродажа выполнена: {amount:.4f} {currency_code} по курсу {rate:.2f} USD/{currency_code}")
    lines.append("\nИзменения в портфеле:")
    lines.append(f"\n- {currency_code}: было {old_balance:.4f} → стало {wallet.balance:.4f}")
    lines.append(f"\nПолучено: {revenue_usd:.2f} USD")

    return {"success": True, "message": "\n".join(lines)}


# 6. Команда на получение курса валют
def get_rate(from_currency: str, to_currency: str) -> Dict[str, Any]:
    """Получает курс одной валюты к другой."""

    # Использование singleton
    settings = SettingsLoader()
    rates_ttl = settings.get("rates_ttl_seconds", 300)
    

    if not from_currency or not from_currency.strip():
        return {"success": False, "message": "\nИсходная валюта не может быть пустой"}
    if not to_currency or not to_currency.strip():
        return {"success": False, "message": "\nЦелевая валюта не может быть пустой"}

    from_curr = from_currency.strip().upper()
    to_curr = to_currency.strip().upper()


        # Проверяем существование валют
    try:
        get_currency(from_curr)
    except CurrencyNotFoundError as e:
        return {"success": False, "message": str(e)}

    try:
        get_currency(to_curr)
    except CurrencyNotFoundError as e:
        return {"success": False, "message": str(e)}


    rates_data = load_json(const.RATES_FILE)


    # Проверка актуальности курсов
    if "last_refresh" in rates_data:
        last_refresh_str = rates_data["last_refresh"]
        
        try:
            # Конвертируем ISO строку в timestamp
            from datetime import datetime
            dt = datetime.fromisoformat(last_refresh_str.replace('Z', '+00:00'))
            last_refresh = int(dt.timestamp())
            
            current_time = int(time.time())
            if (current_time - last_refresh) > rates_ttl:
                return {
                    "success": False, 
                    "message": str(ApiRequestError(
                        f"Курсы устарели. TTL: {rates_ttl} секунд. "
                        f"Последнее обновление: {last_refresh_str}"
                    ))
                }
        except (ValueError, AttributeError) as e:
            # Если не можем распарсить время, считаем данные устаревшими
            return {
                "success": False, 
                "message": str(ApiRequestError(
                    f"Неверный формат времени в rates.json: {last_refresh_str}"
                ))
            }

    pair = f"{from_curr}_{to_curr}"
    rate_info = rates_data.get(pair)


    if rate_info is None:
        return {"success": False, "message": str(ApiRequestError(f"курс {from_curr}→{to_curr} недоступен"))}

    rate = rate_info["rate"]
    updated_at = rate_info.get("updated_at", rates_data.get("last_refresh", "unknown"))

    if rate > 0:
        reverse_rate = 1.0 / rate
    else:
        reverse_rate = 0.0

    lines = []
    lines.append(f"\nКурс {from_curr}→{to_curr}: {rate:.8f} (обновлено: {updated_at})")
    lines.append(f"\nОбратный курс {to_curr}→{from_curr}: {reverse_rate:.8f}")

    print(f'\nКурсы обновляются каждые {rates_ttl} с')
    return {
        "success": True, 
        "message": "\n".join(lines),
        "rate": rate,         
        "updated_at": updated_at 
    }