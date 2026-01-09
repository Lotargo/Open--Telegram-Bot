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
    if services_collection.count_documents({}) == 0:
        initial_services = [
            {
                "name": "Разработка Telegram бота (Базовый)",
                "price_range": "100$ - 300$",
                "description": "Простой бот: ответы на вопросы, кнопки, простая логика."
            },
            {
                "name": "Разработка Telegram бота (Продвинутый)",
                "price_range": "500$ - 1500$",
                "description": "Интеграции с API, базами данных, платежными системами, LLM."
            },
            {
                "name": "Консультация",
                "price_range": "50$ / час",
                "description": "Обсуждение архитектуры, ревью кода, помощь в ТЗ."
            },
            {
                "name": "Сложный/Нестандартный проект",
                "price_range": "По договоренности",
                "description": "Для сложных задач и персональных решений. Свяжитесь с разработчиком: @Lotargo"
            }
        ]
        services_collection.insert_many(initial_services)
        print("Database initialized with default services.")
    else:
        print("Database already contains services.")

def get_services_context():
    """Fetches services and returns a string formatted for the LLM system prompt."""
    db = get_db()
    services = db["services"].find()

    text = "Список услуг и примерные цены:\n"
    for s in services:
        text += f"- {s['name']}: {s['price_range']}. ({s['description']})\n"

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
