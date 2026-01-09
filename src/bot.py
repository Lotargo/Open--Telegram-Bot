import asyncio
import os
import logging
from dotenv import load_dotenv

# Load env vars before importing modules that might use them at module level (like src.handlers -> src.llm)
load_dotenv()

from aiogram import Bot, Dispatcher

from src.handlers import router
from src.middleware import RateLimitMiddleware
from src.database import init_db

# Configure logging
logging.basicConfig(level=logging.INFO)

async def main():
    # Initialize DB (if running locally or ensure it's hit at startup)
    try:
        init_db()
    except Exception as e:
        logging.error(f"DB Init failed (might be expected if mongo container not ready yet): {e}")

    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token or bot_token == "YOUR_TELEGRAM_BOT_TOKEN":
        logging.error("BOT_TOKEN is not set in .env")
        return

    bot = Bot(token=bot_token)
    dp = Dispatcher()

    # Register Middleware
    dp.message.middleware(RateLimitMiddleware(limit=2, window=3)) # 2 msgs per 3 secs

    # Register Routers
    dp.include_router(router)

    logging.info("Starting bot...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Polling error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped by user.")
    except Exception as e:
        logging.exception(f"Unexpected error: {e}")
