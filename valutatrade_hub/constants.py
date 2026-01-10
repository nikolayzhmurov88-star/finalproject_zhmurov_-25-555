from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
USERS_FILE = DATA_DIR / "users.json"
PORTFOLIOS_FILE = DATA_DIR / "portfolios.json"
RATES_FILE = DATA_DIR / "rates.json"

print("DATA_DIR =", DATA_DIR)
print("USERS_FILE =", USERS_FILE)
print("Файл users.json существует:", USERS_FILE.exists())