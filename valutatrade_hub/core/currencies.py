""" Модуль для работы с валютами """

from abc import ABC, abstractmethod # Импортируем инструменты для работы с абстрактными классами
from valutatrade_hub.core.exceptions import CurrencyNotFoundError # Импортируем обработку исключения


class Currency(ABC): # Объявляем абстрактный класс
    """
    Абстрактный базовый класс Currency.
    
    Атрибуты (public):
    name: str — человекочитаемое имя (например, "US Dollar", "Bitcoin").
    code: str — ISO-код или общепринятый тикер ("USD", "EUR", "BTC", "ETH").
    
    Методы:
    get_display_info() -> str — строковое представление для UI/логов.
    
    Инварианты/валидация:
    code — верхний регистр, 2–5 символов, без пробелов.
    name — не пустая строка.
    """
    
    @property # Абстрактное свойство
    @abstractmethod
    def name(self) -> str:
        """Человекочитаемое имя валюты."""
        pass
    
    @property # Абстрактное свойство
    @abstractmethod
    def code(self) -> str:
        """Код/тикер валюты."""
        pass
    
    @abstractmethod # Абстрактный метод
    def get_display_info(self) -> str:
        """Строковое представление для UI/логов."""
        pass

# Метод для фиатных валют
class FiatCurrency(Currency):
    """
    FiatCurrency(Currency):
    Доп. атрибут: issuing_country: str.
    """
    
    def __init__(self, code: str, name: str, issuing_country: str):
        self._code = code.upper()
        self._name = name
        self._issuing_country = issuing_country # Дополнительный атрибут
    
    # Геттеры
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def code(self) -> str:
        return self._code
    
    @property
    def issuing_country(self) -> str:
        return self._issuing_country
    
    # Метод класса
    def get_display_info(self) -> str:
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"


# Метод для криптовалют 
class CryptoCurrency(Currency):
    """
    CryptoCurrency(Currency):
    Доп. атрибуты: algorithm: str, market_cap: float.
    """
    
    def __init__(self, code: str, name: str, algorithm: str, market_cap: float):
        self._code = code.upper()
        self._name = name
        self._algorithm = algorithm # Дополнительный атрибут
        self._market_cap = market_cap # Дополнительный атрибут
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def code(self) -> str:
        return self._code
    
    @property
    def algorithm(self) -> str:
        return self._algorithm
    
    @property
    def market_cap(self) -> float:
        return self._market_cap
    
    # Метод класса
    def get_display_info(self) -> str:
        return f"[CRYPTO] {self.code} — {self.name} (Algo: {self.algorithm}, MCAP: {self.market_cap})"


# Реестр валют
_currencies = {
    "USD": FiatCurrency("USD", "US Dollar", "United States"),
    "EUR": FiatCurrency("EUR", "Euro", "European Union"),
    "RUB": FiatCurrency("RUB", "Russian Ruble", "Russia"),
    "BTC": CryptoCurrency("BTC", "Bitcoin", "SHA-256", 1_000_000_000_000),
    "ETH": CryptoCurrency("ETH", "Ethereum", "Ethash", 400_000_000_000),
    "XRP": CryptoCurrency("XRP", "Ripple", "XRP Ledger", 80_000_000_000)
}

# Функция для обработки неизвестных кодов
def get_currency(code: str) -> Currency:
    """
    Словарь/фабрика для получения валюты по коду.
    """
    code = code.upper()
    if code not in _currencies:
        raise CurrencyNotFoundError(code)  # Используем исключение
    return _currencies[code]


