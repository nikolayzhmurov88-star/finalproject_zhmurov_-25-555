"""
Пользовательские исключения.
"""

# Родительский класс
class ValutaTradeError(Exception):
    """Базовое исключение для всех ошибок ValutaTrade Hub."""
    pass


class InsufficientFundsError(ValutaTradeError):
    """Недостаточно средств"""
    
    def __init__(self, available: float, required: float, code: str):
        self.available = available
        self.required = required
        self.code = code
        message = f"\nНедостаточно средств: доступно {available} {code}, требуется {required} {code}"
        super().__init__(message)


class CurrencyNotFoundError(ValutaTradeError):
    """Неизвестная валюта"""
    
    def __init__(self, code: str):
        self.code = code
        message = f"\nНеизвестная валюта '{code}'"
        super().__init__(message)


class ApiRequestError(ValutaTradeError):
    """Сбой внешнего API"""
    
    def __init__(self, reason: str):
        self.reason = reason
        message = f"\nОшибка при обращении к внешнему API: {reason}"
        super().__init__(message)