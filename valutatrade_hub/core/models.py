# Основные классы программы


# Необходимые импорты
import hashlib # библиотека для хэширования паролей
import secrets # для генерации случайной соли
from datetime import datetime # для обработки даты и времени
from typing import Dict, Any # !!!!


# ========================================================
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
        self._hashed_password = self._hash_password(password) # - пароль хешируем и сохраняем хеш в _hashed_password
        self._registration_date = registration_date or datetime.now().isoformat() # - если дата регистрации не передана, ставим текущее время в формате ISO



    # Геттеры и сеттеры


    @property # Геттер для id полььзователя
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
            raise ValueError("Пароль должен быть не короче 4 символов")
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
            test_hash = self._hash_password(password)
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


### ==========================================================!!!!Код для работы с JSON

    def to_dict(self) -> Dict[str, Any]:
        """Создает словарь для последующей записи в JSON."""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "hashed_password": self._hashed_password,
            "salt": self._salt,
            "registration_date": self._registration_date,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """Создаёт User из словаря прочитанного из JSON."""
        return cls(
            user_id=data["user_id"],
            username=data["username"],
            password="",  # пароль не хранится в открытом виде
            salt=data["salt"],
            registration_date=data["registration_date"],
        )

### ============================================================

class Wallet:
    """Кошелёк пользователя для одной валюты"""

    def __init__(self, currency_code: str, balance: float = 0.0):
        """Создаёт кошелёк для указанной валюты с начальным балансом"""
        self.currency_code = currency_code
        self._balance = 0.0
        self.balance = balance  # используем сеттер

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
        """Снимает средства с кошелька, если баланс позволяет"""
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма должна быть числом")
        if amount <= 0:
            raise ValueError("Сумма снятия должна быть положительной")
        if amount > self.balance:
            raise ValueError("Недостаточно средств на кошельке")
        self.balance -= amount

    def get_balance_info(self) -> dict:
        """Возвращает информацию о текущем балансе"""
        return {
            "currency_code": self.currency_code,
            "balance": self.balance,
        }
# =======================================================================

