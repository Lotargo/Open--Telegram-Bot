import os
from pymongo import MongoClient

# Use 'localhost' if running outside docker (for testing scripts), or 'mongo' service name inside docker
# But for the app running inside docker, it will use the env var which defaults to 'mongodb://mongo:27017/portfolio_bot'
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/portfolio_bot")

def get_db():
    client = MongoClient(MONGO_URI)
    return client.get_database()

def init_db():
    db = get_db()
    services_collection = db["services"]

    # Check if we already have services, if not, seed them
    # Note: To update services, we might need to drop collection or update logic.
    # For now, we will clear and re-insert to reflect the new pricing policy.
    services_collection.delete_many({}) # Reset services to update to new pricing

    initial_services = [
        {
            "name": "Простые боты (автоответчики, скрипты)",
            "price_range": "от 1 500 руб.",
            "description": "Базовая автоматизация, ответы на вопросы, меню. Идеально для старта."
        },
        {
            "name": "AI-Ассистенты",
            "price_range": "6 000 - 10 000 руб. (в среднем)",
            "description": "Умные боты с LLM (как этот). Гибкие ответы, интеграция с AI."
        },
        {
            "name": "Web Apps / Сложные интеграции",
            "price_range": "Индивидуально",
            "description": "Полноценные приложения внутри Telegram, работа с базами данных и API."
        },
        {
            "name": "Техническая поддержка",
            "price_range": "Обсуждается отдельно",
            "description": "Поддержка, доработка и улучшение функционала после сдачи проекта."
        }
    ]
    services_collection.insert_many(initial_services)
    print("Database initialized with updated services.")

def get_services_context():
    """Fetches services and returns a string formatted for the LLM system prompt."""
    db = get_db()
    services = db["services"].find()

    text = "Информация о ценах и услугах:\n"
    text += "Мы предлагаем разработку Telegram-ботов по ценам в среднем в 2 раза ниже рыночных.\n\n"

    text += "**Прайс-лист (ориентировочный):**\n"
    for s in services:
        text += f"- {s['name']}: {s['price_range']}. {s['description']}\n"

    text += "\n**Важно знать:**\n"
    text += "- **Индивидуальный подход:** Чем интереснее задача, тем гибче цена. Цены ориентировочные и зависят от ваших 'хотелок'.\n"
    text += "- **Хостинг и Ключи:** Мы не продаем хостинг и ключи, но **бесплатно** поможем найти самые выгодные (или бесплатные) варианты и настроить работу 24/7.\n"
    text += "- **Связь:** По сложным вопросам бот перенаправит вас к разработчику (@Lotargo).\n"

    return text

# --- User Management ---

def save_user(user_id, data):
    """Saves or updates user data in the 'users' collection."""
    db = get_db()
    db["users"].update_one(
        {"user_id": user_id},
        {"$set": data},
        upsert=True
    )

def get_user(user_id):
    """Retrieves user data by user_id. Returns None if not found."""
    db = get_db()
    return db["users"].find_one({"user_id": user_id})

def delete_user(user_id):
    """Deletes a user from the 'users' collection."""
    db = get_db()
    result = db["users"].delete_one({"user_id": user_id})
    return result.deleted_count > 0

if __name__ == "__main__":
    # Allow running this file directly to seed DB locally
    init_db()
    print(get_services_context())
