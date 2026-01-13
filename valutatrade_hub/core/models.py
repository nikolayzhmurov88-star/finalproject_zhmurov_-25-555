# Основные классы программы

# Необходимые импорты
import hashlib # библиотека для хэширования паролей
import secrets # для генерации случайной соли
import json # для работы с JSON
from datetime import datetime # для обработки даты и времени
from typing import Dict, Any # для аннотаций
import valutatrade_hub.constants as const # Импорт констант с путями к файлам JSON
from valutatrade_hub.core.exceptions import InsufficientFundsError # Импортируем исключение


class User:
    """Пользователь системы"""

    def __init__(
        self,
        user_id: int,
        username: str,
        password: str,
        salt: str = None,
        registration_date: str = None,
    ):
        """
        Инициализация объекта пользователя.

        Параметры (переменные, передаваемые при создании объекта):
        - user_id: идентификатор пользователя (целое число)
        - username: имя пользователя (строка)
        - password: пароль (строка)
        - salt: соль для хеширования (строка, опционально, по умолчанию None)
        - registration_date: дата регистрации (строка в формате ISO, опционально)

        Эти параметры используются для настройки полей конкретного объекта User.
        """
        # Сохраняем переданные данные в поля объекта:
        self._user_id = user_id # - user_id кладём в приватное поле _user_id 
        self.username = username # - username устанавливаем через сеттер
        self._salt = salt or secrets.token_hex(16) # - если salt не передан, генерируем случайную соль
        self.password = password  # - пароль хешируем и сохраняем хеш в _hashed_password
        self._registration_date = registration_date or datetime.now().isoformat() # - если дата регистрации не передана, ставим текущее время

    # Геттеры и сеттеры

    @property # Геттер для id пользователя
    def user_id(self) -> int:
        """Получить ID пользователя"""
        return self._user_id

    @property # Геттер для имени пользователя
    def username(self) -> str:
        """Получить имя пользователя"""
        return self._username

    @username.setter # Сеттер для имени пользователя
    def username(self, value: str) -> None:
        """Установить имя пользователя с проверкой"""
        if not value or not value.strip():
            raise ValueError("Имя пользователя не может быть пустым")
        self._username = value.strip()

    @property # Геттер для пароля
    def password(self) -> str:
        """Возвращает хеш пароля (открытый пароль недоступен)."""
        return self._hashed_password

    @password.setter # Сеттер для пароля (проверка и хеширование)
    def password(self, value: str) -> None: 
        """Устанавливает пароль: проверяет длину и хеширует."""
        if len(value) < 4:
            raise ValueError("\nПароль должен быть не короче 4 символов")
        # Хешируем пароль с солью
        salted = f"{self._salt}{value}".encode("utf-8")
        self._hashed_password = hashlib.sha256(salted).hexdigest()

    @property # Геттер для даты регистрации
    def registration_date(self) -> str:
        """Получить дату регистрации"""
        return self._registration_date

   
    # Методы работы с паролем
    def verify_password(self, password: str) -> bool: # Метод проверки пароля пользователя
        """Проверяет, совпадает ли введённый пароль с сохранённым хешем"""
        try:
             # Собираем salt + password и считаем хеш
            salted = f"{self._salt}{password}".encode("utf-8")
            test_hash = hashlib.sha256(salted).hexdigest()
            return test_hash == self._hashed_password
        except ValueError:
            return False

    def change_password(self, new_password: str) -> None: # Метод изменяет пароль пользователя
        """Изменяет пароль пользователя."""
        self.password = new_password  # вызовется сеттер с проверкой

    # Работа с данными пользователя
    def get_user_info(self) -> Dict[str, Any]:
        """Возвращает информацию о пользователе (без пароля)"""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date,
        }


    # Код для работы с JSON
    def to_dict(self) -> Dict[str, Any]:
        """Создает словарь для последующей записи в JSON."""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "hashed_password": self._hashed_password,
            "salt": self._salt,
            "registration_date": self._registration_date,
        }

    # Получаем данные из JSON и создаем объект
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        user = cls.__new__(cls)  
        user._user_id = data["user_id"]
        user._username = data["username"]
        user._hashed_password = data["hashed_password"]
        user._salt = data["salt"]
        user._registration_date = data["registration_date"]
        return user



class Wallet:
    """Кошелёк пользователя для одной валюты"""

    def __init__(self, currency_code: str, balance: float = 0.0):
        """Создаёт кошелёк для указанной валюты с начальным балансом"""
        self.currency_code = currency_code
        self._balance = 0.0
        self.balance = balance 

    # Геттер и сеттер balance
    @property
    def balance(self) -> float:
        """Возвращает текущий баланс кошелька"""
        return self._balance

    @balance.setter
    def balance(self, value: float) -> None:
        """Устанавливает баланс, отрицательные значения и некорректные типы"""
        if not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным")
        self._balance = float(value)


    # Методы работы с кошельком
    def deposit(self, amount: float) -> None:
        """Пополняет баланс кошелька"""
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма должна быть числом")
        if amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительной")
        self.balance += amount

    def withdraw(self, amount: float) -> None:
        if not isinstance(amount, (int, float)):
            raise TypeError("\Сумма должна быть числом")
        if amount <= 0:
            raise ValueError("\Сумма снятия должна быть положительной")
        if amount > self.balance:
            raise InsufficientFundsError(  # Вызываем исключение
                available=self.balance,
                required=amount,
                code=self.currency_code
            )
        self.balance -= amount

    def get_balance_info(self) -> dict:
        """Возвращает информацию о текущем балансе"""
        return {
            "currency_code": self.currency_code,
            "balance": self.balance,
        }


class Portfolio:
    """Управление всеми кошельками одного пользователя"""

    def __init__(self, user_id: int, wallets: dict = None):
        """Создаёт портфель для пользователя с указанными кошельками"""
        self._user_id = user_id
        self._wallets = wallets or {}

    # Геттеры

    @property
    def user(self) -> int:
        """Возвращает идентификатор пользователя (без возможности перезаписи)"""
        return self._user_id

    @property
    def wallets(self) -> dict:
        """Возвращает копию словаря кошельков"""
        return self._wallets.copy()

    # Методы работы с валютами

    def add_currency(self, currency_code: str) -> None:
        """Добавляет новый кошелёк в портфель, если его ещё нет"""
        if currency_code in self._wallets:
            raise ValueError(f"\nВалюта {currency_code} уже есть в портфеле")
        self._wallets[currency_code] = Wallet(currency_code=currency_code, balance=0.0)

    def get_wallet(self, currency_code: str) -> Wallet:
        """Возвращает объект Wallet по коду валюты"""
        if currency_code not in self._wallets:
            raise KeyError(f"\nВалюта {currency_code} не найдена в портфеле")
        return self._wallets[currency_code]

    
    def get_total_value(self, base_currency: str = "USD") -> float:
        """
        Возвращает общую стоимость портфеля в указанной базовой валюте.
        1. Считаем всё в USD
        2. Конвертируем USD → base_currency
        """
        try:
            # Загружаем курсы
            with open(const.RATES_FILE, 'r', encoding='utf-8') as f:
                rates_data = json.load(f)
            
            if not isinstance(rates_data, dict) or "pairs" not in rates_data:
                return 0.0
            
            pairs = rates_data.get("pairs", {})
            
            # 1. Считаем всё в USD
            total_usd = 0.0
            
            for currency, wallet in self._wallets.items():
                balance = wallet.balance
                
                if currency == "USD":
                    total_usd += balance
                else:
                    # Ищем курс к USD
                    pair_to_usd = f"{currency}_USD"
                    rate_info = pairs.get(pair_to_usd)
                    
                    if rate_info and "rate" in rate_info:
                        total_usd += balance * rate_info["rate"]
                    else:
                        # Обратный курс
                        reverse_pair = f"USD_{currency}"
                        reverse_info = pairs.get(reverse_pair)
                        if reverse_info and "rate" in reverse_info and reverse_info["rate"] > 0:
                            total_usd += balance / reverse_info["rate"]
            
            # 2. Если нужна USD, возвращаем
            if base_currency == "USD":
                return total_usd
            
            # 3. Конвертируем в base_currency
            usd_to_base = f"USD_{base_currency}"
            base_to_usd = f"{base_currency}_USD"
            
            usd_to_base_info = pairs.get(usd_to_base)
            if usd_to_base_info and "rate" in usd_to_base_info:
                return total_usd * usd_to_base_info["rate"]
            
            base_to_usd_info = pairs.get(base_to_usd)
            if base_to_usd_info and "rate" in base_to_usd_info and base_to_usd_info["rate"] > 0:
                return total_usd / base_to_usd_info["rate"]
            
            # Курс не найден
            return total_usd
            
        except Exception:
            return 0.0


    # Методы для работы с JSON 
    def to_dict(self) -> Dict[str, Any]:
        """Создает словарь для последующей записи в JSON."""
        return {
            "user_id": self._user_id,
            "wallets": {
                currency_code: {"balance": wallet.balance}
                for currency_code, wallet in self._wallets.items()
            }
        }

    # Считывает портфолию из JSON
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Portfolio":
        """Создает объект Portfolio из словаря."""
        portfolio = cls.__new__(cls)
        portfolio._user_id = data["user_id"]

        wallets = {}
        for currency_code, wallet_data in data["wallets"].items():
            balance = wallet_data["balance"]
            wallet = Wallet(currency_code=currency_code, balance=balance)
            wallets[currency_code] = wallet

        portfolio._wallets = wallets
        return portfolio
