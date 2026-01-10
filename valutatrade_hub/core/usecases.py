"""Бизнес-логика"""

import json # Для работы с JSON
from typing import Dict, Any # для аннотаций
import valutatrade_hub.constants as const # Импорт констант с путями к файлам
from valutatrade_hub.core.models import User, Portfolio # Импорт основных классов программы


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



# 1. Команда регистрации
def register_user(username: str, password: str) -> Dict[str, Any]:
    """Регистрирует нового пользователя."""
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



# 2. Команда входа в систему
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
def buy_currency(user_id: int, currency_code: str, amount: float) -> Dict[str, Any]:
    """Покупает валюту"""
    if not currency_code or not currency_code.strip():
        return {"success": False, "message": "Код валюты не может быть пустым"}
    currency_code = currency_code.strip().upper()

    if not isinstance(amount, (int, float)) or amount <= 0:
        return {"success": False, "message": "'amount' должен быть положительным числом"}

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
        return {"success": False, "message": "\nФайл rates.json повреждён или пустой"}

    # Ищем пару currency_code → USD
    pair = f"{currency_code}_USD"
    rate_info = rates_data.get(pair)

    if rate_info is None:
        return {"success": False, "message": f"\nНе удалось получить курс для {currency_code}→USD"}

    if not isinstance(rate_info, dict) or "rate" not in rate_info:
        return {"success": False, "message": f"\nНеверный формат курса для {currency_code}→USD"}

    rate = rate_info["rate"]
    cost_usd = amount * rate

    # Работаем с кошельками через методы Portfolio
    try:
        # Получаем USD-кошелёк
        usd_wallet = portfolio.get_wallet("USD")
        if usd_wallet.balance < cost_usd:
            return {
                "success": False,
                "message": f"\nНедостаточно средств: требуется {cost_usd:.2f} USD, доступно {usd_wallet.balance:.2f} USD"
            }

        # Добавляем валюту, если её ещё нет
        if currency_code not in portfolio._wallets:
            portfolio.add_currency(currency_code)

        # Получаем кошелёк валюты
        target_wallet = portfolio.get_wallet(currency_code)
        old_balance = target_wallet.balance

        # Списываем USD и пополняем валюту
        usd_wallet.balance -= cost_usd
        target_wallet.balance += amount

        # Сохраняем обновлённый портфель
        portfolio_data["wallets"] = {k: {"balance": v.balance} for k, v in portfolio._wallets.items()}
        save_json(const.PORTFOLIOS_FILE, {"portfolios": portfolios})

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
def sell_currency(user_id: int, currency_code: str, amount: float) -> Dict[str, Any]:
    """Продаёт валюту"""
    if not currency_code or not currency_code.strip():
        return {"success": False, "message": "Код валюты не может быть пустым"}
    currency_code = currency_code.strip().upper()

    if not isinstance(amount, (int, float)) or amount <= 0:
        return {"success": False, "message": "'amount' должен быть положительным числом"}

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
    wallet = portfolio.get_wallet(currency_code)
    if wallet.balance < amount:
        return {"success": False, "message": f"\nНедостаточно средств: требуется {amount:.4f} {currency_code}, доступно {wallet.balance:.4f} {currency_code}"}

    # Получаем курс из rates.json
    rates_data = load_json(const.RATES_FILE)
    if not isinstance(rates_data, dict):
        return {"success": False, "message": "\nФайл rates.json повреждён или пустой"}

    # Ищем пару currency_code → USD
    pair = f"{currency_code}_USD"
    rate_info = rates_data.get(pair)

    if rate_info is None:
        return {"success": False, "message": f"\nНе удалось получить курс для {currency_code}→USD"}

    if not isinstance(rate_info, dict) or "rate" not in rate_info:
        return {"success": False, "message": f"\nНеверный формат курса для {currency_code}→USD"}

    rate = rate_info["rate"]
    revenue_usd = amount * rate

    # Сохраняем старый баланс
    old_balance = wallet.balance

    # Списываем валюту и пополняем USD
    wallet.balance -= amount
    usd_wallet = portfolio.get_wallet("USD")
    usd_wallet.balance += revenue_usd

    # Сохраняем обновлённый портфель
    portfolio_data["wallets"] = {k: {"balance": v.balance} for k, v in portfolio._wallets.items()}
    save_json(const.PORTFOLIOS_FILE, {"portfolios": portfolios})

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
    if not from_currency or not from_currency.strip():
        return {"success": False, "message": "\nИсходная валюта не может быть пустой"}
    if not to_currency or not to_currency.strip():
        return {"success": False, "message": "\nЦелевая валюта не может быть пустой"}

    from_curr = from_currency.strip().upper()
    to_curr = to_currency.strip().upper()

    rates_data = load_json(const.RATES_FILE)
    pair = f"{from_curr}_{to_curr}"
    rate_info = rates_data.get(pair)

    if rate_info is None:
        return {"success": False, "message": f"\nКурс {from_curr}→{to_curr} недоступен. Повторите попытку позже."}

    rate = rate_info["rate"]
    updated_at = rate_info.get("updated_at", rates_data.get("last_refresh", "unknown"))

    if rate > 0:
        reverse_rate = 1.0 / rate
    else:
        reverse_rate = 0.0

    lines = []
    lines.append(f"\nКурс {from_curr}→{to_curr}: {rate:.8f} (обновлено: {updated_at})")
    lines.append(f"\nОбратный курс {to_curr}→{from_curr}: {reverse_rate:.8f}")

    return {"success": True, "message": "\n".join(lines)}
