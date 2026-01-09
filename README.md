# AI Portfolio Bot

Telegram бот-визитка, который работает как "умный секретарь". Бот использует LLM (Groq) для ответов на вопросы о услугах и ценах, а также для оформления заявок от клиентов.

## Функционал

*   **Умный секретарь:** Отвечает на вопросы, используя прайс-лист из базы данных и инструкции из `config/system_prompt.j2`.
*   **Заявки:** Собирает данные клиента и формирует карточку заявки. Использует JSON для надежного парсинга ответов LLM.
*   **Сбор Контактов:** Поддерживает кнопку "Поделиться контактом" для быстрого ввода телефона.
*   **Подтверждение:** Требует явного подтверждения от пользователя (Инлайн-кнопка) перед отправкой админу.
*   **Rate Limiting:** Защита от спама (настраивается в `config/bot_config.yaml`).
*   **Конфигурация:** Все настройки (модель, температура, промпты) вынесены в папку `config/`.

## Быстрый старт (Скрипты)

Для вашего удобства мы подготовили скрипты установки и запуска.

### Linux / macOS

1.  **Установка (Poetry + .env):**
    ```bash
    ./scripts/linux/setup.sh
    ```
2.  **Запуск (Локально):**
    ```bash
    ./scripts/linux/run.sh
    ```
3.  **Запуск (Docker):**
    ```bash
    ./scripts/linux/docker_run.sh
    ```

### Windows

1.  **Установка (Poetry + .env):**
    Запустите `scripts\windows\setup.bat`
2.  **Запуск (Локально):**
    Запустите `scripts\windows\run.bat`
3.  **Запуск (Docker):**
    Запустите `scripts\windows\docker_run.bat`

## Ручная Установка

1.  **Создайте .env файл:**
    ```env
    BOT_TOKEN=ваш_токен_бота
    ADMIN_GROUP_ID=
    GROQ_API_KEY=ваш_ключ_groq
    MONGO_URI=mongodb://mongo:27017/portfolio_bot
    ```

2.  **Poetry:**
    ```bash
    poetry install
    source .venv/bin/activate
    ```

3.  **Docker:**
    ```bash
    docker-compose up --build -d
    ```

## Настройка Админа

1.  Добавьте бота в группу или напишите ему лично.
2.  Напишите команду `/set_admin`.
3.  Бот пришлет ID чата. Вставьте этот ID в `.env` файл (`ADMIN_GROUP_ID`).
4.  Перезапустите бота.

## Разработка

*   **Config:**
    *   `config/llm_config.yaml`: Модель, параметры LLM.
    *   `config/system_prompt.j2`: Системный промпт (Jinja2 шаблон).
    *   `config/bot_config.yaml`: Лимиты, логирование.

## Стек

*   Python 3.11+
*   Poetry (Dependency Management)
*   Aiogram 3.x
*   MongoDB (pymongo)
*   OpenAI SDK (Async)
*   Jinja2 (Templating)
*   Docker & Docker Compose
