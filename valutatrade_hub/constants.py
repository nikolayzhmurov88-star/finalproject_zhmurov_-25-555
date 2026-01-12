"""
Константы проекта
"""

from pathlib import Path
from valutatrade_hub.infra.settings import SettingsLoader

# Singleton с настройками
settings = SettingsLoader()

# Из config.json через SettingsLoader
DATA_DIR = Path(settings.get("data_dir"))
USERS_FILE = Path(settings.get("users_file"))
PORTFOLIOS_FILE = Path(settings.get("portfolios_file"))
RATES_FILE = Path(settings.get("rates_file"))
RATES_TTL_SECONDS = settings.get("rates_ttl_seconds")
DEFAULT_BASE_CURRENCY = settings.get("default_base_currency")
STARTING_BALANCE = settings.get("starting_balance")
MIN_PASSWORD_LENGTH = settings.get("min_password_length")
LOG_DIR = Path(settings.get("log_dir"))
LOG_FORMAT = settings.get("log_format")

# Проверяем обязательные поля
required_fields = [
    "data_dir", "users_file", "portfolios_file", "rates_file",
    "rates_ttl_seconds", "default_base_currency", "starting_balance"
]

for field in required_fields:
    if settings.get(field) is None:
        raise ValueError(f"Обязательное поле '{field}' отсутствует в config.json")

# Создаём директории
DATA_DIR.mkdir(exist_ok=True, parents=True)
LOG_DIR.mkdir(exist_ok=True, parents=True)