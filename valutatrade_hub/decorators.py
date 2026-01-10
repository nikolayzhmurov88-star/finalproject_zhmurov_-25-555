"""
Декораторы для ValutaTrade Hub.
"""

import logging
from datetime import datetime
from functools import wraps
from typing import Callable, Any, Dict, Optional


def log_action(action: str, verbose: bool = False):
    """
    Декоратор для логирования доменных операций.
    
    Args:
        action: Тип действия (BUY, SELL, REGISTER, LOGIN, etc.)
        verbose: Подробное логирование с контекстом
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Получаем логгер
            logger = logging.getLogger("valutatrade")
            
            # Базовые данные для лога
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "action": action,
                "result": "OK",
                "error_type": None,
                "error_message": None
            }
            
            # Извлекаем параметры из аргументов функции
            try:
                # Для buy_currency и sell_currency
                if action in ["BUY", "SELL"]:
                    user_id = args[0] if len(args) > 0 else kwargs.get('user_id')
                    currency_code = args[1] if len(args) > 1 else kwargs.get('currency_code')
                    amount = args[2] if len(args) > 2 else kwargs.get('amount')
                    
                    log_data.update({
                        "user_id": user_id,
                        "currency_code": currency_code,
                        "amount": amount
                    })
                
                # Для register_user и login_user
                elif action in ["REGISTER", "LOGIN"]:
                    username = args[0] if len(args) > 0 else kwargs.get('username')
                    log_data["username"] = username
                
                # Для других действий
                else:
                    log_data["params"] = str(args) if args else str(kwargs)
                
            except (IndexError, KeyError):
                # Если не удалось извлечь параметры
                log_data["params"] = str(args) if args else str(kwargs)
            
            try:
                # Выполняем функцию
                result = func(*args, **kwargs)
                
                # Извлекаем дополнительные данные из результата
                if isinstance(result, dict):
                    if result.get("success"):
                        log_data["result"] = "OK"
                        # Для buy/sell можно извлечь rate из сообщения
                        if action in ["BUY", "SELL"] and "message" in result:
                            msg = result["message"]
                            if "по курсу" in msg:
                                # Парсим курс из сообщения
                                import re
                                rate_match = re.search(r'по курсу (\d+\.?\d*)', msg)
                                if rate_match:
                                    log_data["rate"] = rate_match.group(1)
                                    log_data["base"] = "USD"  # Пока только USD
                    else:
                        log_data["result"] = "ERROR"
                        log_data["error_message"] = result.get("message", "Unknown error")
                
                # Логируем успех
                log_message = format_log_message(log_data, verbose)
                logger.info(log_message)
                
                return result
                
            except Exception as e:
                # Логируем исключение
                log_data.update({
                    "result": "ERROR",
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                })
                
                log_message = format_log_message(log_data, verbose)
                logger.error(log_message)
                
                # Пробрасываем исключение дальше
                raise
        
        return wrapper
    return decorator


def format_log_message(log_data: Dict[str, Any], verbose: bool = False) -> str:
    """Форматирует сообщение лога."""
    if verbose:
        # Подробный формат
        parts = [f"{log_data['action']}"]
        
        if "user_id" in log_data:
            parts.append(f"user_id={log_data['user_id']}")
        elif "username" in log_data:
            parts.append(f"username={log_data['username']}")
            
        if "currency_code" in log_data:
            parts.append(f"currency={log_data['currency_code']}")
        if "amount" in log_data:
            parts.append(f"amount={log_data['amount']}")
        if "rate" in log_data:
            parts.append(f"rate={log_data['rate']}")
        if "base" in log_data:
            parts.append(f"base={log_data['base']}")
            
        parts.append(f"result={log_data['result']}")
        
        if log_data["result"] == "ERROR":
            parts.append(f"error={log_data['error_type']}:{log_data['error_message']}")
            
        return " ".join(parts)
    
    else:
        # Компактный формат
        message = f"{log_data['action']}"
        
        if "user_id" in log_data:
            message += f" user_id={log_data['user_id']}"
        if "currency_code" in log_data:
            message += f" currency={log_data['currency_code']}"
        if "amount" in log_data:
            message += f" amount={log_data['amount']}"
            
        message += f" result={log_data['result']}"
        
        if log_data["result"] == "ERROR" and log_data["error_type"]:
            message += f" error={log_data['error_type']}"
            
        return message