## ValutaTrade Hub - Менеджер криптовалютного портфеля

Описание проекта:
ValutaTrade Hub - это консольное приложение для управления инвестиционным портфелем криптовалют и фиатных валют. Программа позволяет пользователям регистрироваться, покупать и продавать валюты, отслеживать курс в режиме реального времени и управлять своими активами.

Основные возможности:
Регистрация и аутентификация пользователей

Покупка и продажа криптовалют (BTC, ETH, XRP) и фиатных валют (USD, EUR, RUB)

Отображение портфеля с расчетом общей стоимости в базовой валюте

Получение актуальных курсов валют из внешних API

Автоматическое обновление курсов

Логирование всех операций


## Установка из GitHub
Клонируйте репозиторий:

- git clone https://github.com/nikolayzhmurov88-star/finalproject_zhmurov_-25-555.git

- cd finalproject_zhmurov_-25-555

Установите зависимости с помощью Poetry:

- make install

Настройте переменную окружения для API-ключа:

- export EXCHANGERATE_API_KEY="ваш_ключ_здесь"

Для запуска:

- make project

Альтернативная установка
После клонирования репозитория вы также можете установить пакет:

- make build
- make package-install

## Использование программы
После запуска вы увидите приглашение командной строки. Доступные команды:

Регистрация и вход:

- register --username "имя_пользователя" --password "пароль"

- login --username "имя_пользователя" --password "пароль"

- logout

При регистрации каждому пользователю начисляется стартовый баланс 100,000 USD.

Управление портфелем:

- show-portfolio --base USD          # Показать портфель в указанной валюте

- buy --currency BTC --amount 0.5      # Купить валюту

- sell --currency ETH --amount 1.0     # Продать валюту

Работа с курсами валют:

- get-rate --from USD --to BTC         # Получить курс валюты

- update-rates [--source coingecko|exchangerate]  # Обновить курсы

- show-rates [--currency BTC] [--top 5] [--base USD]  # Показать курсы из кеша


Выход из программы:

- exit

## Тестирование функциональности:

1. Регистрация нового пользователя
register --username "testuser" --password "testpass123"

2. Вход в систему
login --username "testuser" --password "testpass123"

3. Обновление курсов валют
update-rates

Или из конкретного источника:

- update-rates --source coingecko

- update-rates --source exchangerate

4. Просмотр доступных курсов

- show-rates                    # Все курсы
- show-rates --currency BTC    # Только курс Bitcoin

5. Получение конкретного курса
- get-rate --from USD --to BTC
- get-rate --from EUR --to USD

6. Покупка валюты

- buy --currency BTC --amount 0.1
- buy --currency EUR --amount 500

7. Продажа валюты
- sell --currency BTC --amount 0.05
- sell --currency ETH --amount 0.5

8. Просмотр портфеля
- show-portfolio
- show-portfolio --base EUR
- show-portfolio --base BTC


Требования к API-ключам

Для работы с ExchangeRate-API требуется бесплатный API-ключ:

Зарегистрируйтесь на сайте https://www.exchangerate-api.com/

Получите бесплатный API-ключ

Установите его как переменную окружения EXCHANGERATE_API_KEY


## Демонстрация работы программы
https://asciinema.org/a/0l4vRV9ZW9bkv7uI


## Контакты
Автор: NickZ (nikolayzhmurov88@gmail.com)

GitHub: https://github.com/nikolayzhmurov88-star/finalproject_zhmurov_-25-555.git