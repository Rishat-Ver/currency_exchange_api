# Currency Exchange API

**Currency Exchange Api** — веб-приложение, созданное на основе FastAPI, предназначенное для облегчения доступа к актуальным данным о курсах валют и выполнения операций, связанных с конвертацией валют в реальном времени.
Приложение интегрируется с внешними API обменных курсов, что обеспечивает его актуальность и надежность предоставляемых данных.


![мем](https://cs4.pikabu.ru/post_img/big/2014/10/28/4/1414475770_256512152.jpg)
## Содержание

- [Возможности](#возможности)
- [Структура проекта](#структура-проекта)
- [Установка и запуск проекта](#установка-и-запуск-проекта)
- [API Endpoints](#api-endpoints)
- [Доступ к Swagger UI](#доступ-к-swagger-ui)


## Возможности


**Основные возможности:**
* Аутентификация и безопасность
* Актуальные курсы валют
* Конвертация валют
* Поддержка основго списка мировых валют
* Регистрация и аутентификация пользователей
* Использование WebSocket для мгновенного обновления данных о валютных курсах и операциях конвертации, улучшая взаимодействие пользователя с приложением.
* Доступ к админ-панели
* Кэширование с помощью Redis
* Лимит запросов от пользователей

## Структура проекта

```
currency_exchange_api/
├── alembic/
│   ├── versions/
│   └── env.py
├── app/
│   ├── api/
│   │   ├── admin/
│   │   ├── auth/
│   │   └── endpoints/
│   ├── commands/
│   ├── core/
│   ├── exceptions/
│   ├── media/
│   ├── models/
│   ├── schemas/
│   └── services/
│   └── utils/
├── docker/
├── tests/
├── .env
├── .gitignore
├── alembic.ini
├── docker-compose.yaml
├── Dockerfile
├── LICENSE
├── main.py
├── poetry.lock
├── pyproject.toml
├── README.md
└── requirements.txt
```
## Установка и запуск проекта

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/Rishat-Ver/currency_exchange_api.git
   ```
2. Перейдите в папку проекта:
   ```bash
   cd currency_exchange_api
   ```
3. Создайте виртуальное окружение (рекомендуется):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows, use venv\Scripts\activate.bat
   ```
   
4. Переименовать шаблон-файл переменных окружения `.env.example` в `.env`. 
   
   Ввести свои настройки в .env (с настройками по-умолчанию не безопасно).
   
   Для получения API-key требуется регистрация на https://apilayer.com/
   Выбрать Free Plan на https://apilayer.com/marketplace/currency_data-api
5.  Запустите Docker Compose:
   ```bash
   docker-compose up --build --remove-orphans
   ```
_Примечания:_

_В контейнере поднимается БД, redis и само приложение._

_Создаётся тестовый суперпользователь admin с паролем admin(можно поменять эти значения)._

#### Приложение готово к работе по адресу **http://localhost:8001/**

## API Endpoints

### Авторизация

`POST /api/auth/login/` Авторизует пользователя и возвращает JWT токен для доступа к защищенным маршрутам.

### Обмен валют, требуется авторизация для всех эндпоинтов

- `GET /api/currency/exchange_rate` - Получение актуальных курсов обмена валют относительно базовой валюты (по умолчанию USD).

- `GET /api/currency/show_convert` - Конвертация указанной суммы из одной валюты в другую на заданную дату.

- `GET /api/currency/show_change` - Показывает изменение курса валют за определенный период времени.

- `GET /api/currency/historical` - Возвращает исторические курсы валют для заданной даты.

- `GET /api/currency/list` - Выводит список доступных валют и соответствующих стран.

- `GET /api/currency/timeframe` - Запрашивает курсы валют за определенный период времени. Требует аутентификации.

### Пользователи

- `POST /api/users/create` - Регистрация пользователя с возможностью загрузки изображения профиля.

- `GET /api/users/me` - Получение данных о профиле и балансе текущего пользователя. Требуется аутентификация.

- `PATCH /api/users/top_up_balance/` - Позволяет пользователю пополнить свой баланс. Требуется аутентификация.

- `PATCH /api/users/change_currency/` - Конвертация валютного баланса из одной валюты в другую. Требуется аутентификация.

- `DELETE /api/users/me/delete` - Удаление учетной записи пользователя. Требуется аутентификация.

- `GET /api/users/evaluate_balance` - Оценка суммарного баланса пользователя в выбранной валюте. Требуется аутентификация.

### WebSocket подключение для пользователей

- `WS /api/users/ws/` - Устанавливает соединение WebSocket обновления статуса баланса пользователя в реальном времени. Требуется аутентификация.

После успешного установления соединения через WebSocket, приложение обеспечивает двусторонний канал связи между сервером и клиентом, позволяя отправлять и получать сообщения в реальном времени.

#### Операции с уведомлениями через WebSocket:

- **Пополнение баланса:**
  Когда пользователь пополняет свой баланс, через установленное WebSocket соединение отсылается уведомление с информацией о успешном пополнении.

- **Конвертация валюты:**
  При успешной конвертации валюты пользователя отправляется сообщение через WebSocket, информирующее о деталях совершенной транзакции, включая исходную и целевую валюту, а также сумму конвертации.


#### Особенности:
- Аутентификация пользователя с использованием токена, полученного при входе.
- Управление подключениями с помощью `WebSocketManager`.
- Ограничение частоты сообщений (Rate Limiter) — пользователь может отправлять сообщения не чаще одного раза в 5 секунд.

#### Обработка ошибок:
- При превышении лимита отправки сообщений пользователю будет отправлено уведомление об этом.
- В случае неожиданного разрыва соединения WebSocket со стороны пользователя, `WebSocketManager` отключит пользователя.

## Доступ к Swagger UI

После запуска API вы можете получить доступ к Swagger UI по следующему URL:

```bash
http://localhost:8001/docs
```

Используйте Swagger UI для:

1. **Просмотра конечных точек**
2. **Отправки запросов**
3. **Просмотра ответов**
4. **Тестовые проверки**

**Для тестирования с помощью Swagger UI выполните следующие действия для каждой конечной точки, описанной выше:**

1. Откройте ваш веб-браузер и перейдите по указанному выше пути `/docs`.

2. Изучите доступные конечные точки и выберите ту, которую вы хотите протестировать.

3. Нажмите на кнопку "Try it out" для открытия интерактивной формы, где вы можете ввести данные.

4. Заполните необходимые параметры и тело запроса (если применимо) согласно документации API, приведенной выше.

5. Нажмите кнопку "Execute", чтобы отправить запрос на API.

6. Ответ будет отображен ниже, показывая код состояния и данные ответа.

7. Вы также можете просмотреть примеры запросов и ответов, что может быть полезно для понимания ожидаемого формата данных.

## Использованные инструменты

Проект **Currency Exchange App** построен на основе множества мощных инструментов и библиотек:

* [FastAPI](https://fastapi.tiangolo.com/) - веб-фреймворк приложения.
* [Pydantic](https://pydantic-docs.helpmanual.io/) - для валидации и управления данными на основе аннотации типов.
* [SQLAlchemy](https://www.sqlalchemy.org/) - для работы с базами данных через ORM и асинхронный SQL.
* [AsyncPG](https://magicstack.github.io/asyncpg/current/) - асинхронный драйыер для работы с PostgreSQL.
* [Alembic](https://alembic.sqlalchemy.org/en/latest/) - инструмент миграций для SQLAlchemy.
* [PyJWT](https://pyjwt.readthedocs.io/en/latest/) - реализация JWT для безопасной работы с токенами аутентификации.
* [AIOHTTP](https://docs.aiohttp.org/en/stable/) - асинхронный HTTP-клиент/сервер для модуля asyncio.
* [FastAPI Cache2](https://pypi.org/project/fastapi-cache2/) - кэширование для FastAPI с поддержкой Redis.
* [SQLAdmin](https://pypi.org/project/sqladmin/) - админ-панель для FastAPI и SQLAlchemy.
* [Googletrans](https://py-googletrans.readthedocs.io/en/latest/) - Python клиент для Google Translate API.
* [FastAPI Limiter](https://pypi.org/project/fastapi-limiter/) - для установки лимитов на запросы к API.
* [Docker](https://www.docker.com/) - для контейнеризации и развертывания приложения.
* [Poetry](https://python-poetry.org/) - для управления зависимостями и пакетами.

## Авторы
* [Дарья Коннова](https://github.com/dazdik/)
* [Ришат Вергасов](https://github.com/Rishat-Ver)