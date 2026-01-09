import asyncio
import os
import re
from dotenv import load_dotenv
from aiogram import Bot

# Manually add src to path to import modules
import sys
sys.path.append(os.path.join(os.getcwd(), ''))

from src.llm import LLMClient

# Load env vars
load_dotenv()

async def simulate_conversation():
    print("--- STARTING SIMULATION ---\n")

    # 1. Initialize Components
    llm = LLMClient()
    bot_token = os.getenv("BOT_TOKEN")
    admin_id = os.getenv("ADMIN_GROUP_ID")

    print(f"Config: Bot Token exists? {bool(bot_token)}")
    print(f"Config: Admin ID: {admin_id}")

    if not bot_token or not admin_id:
        print("ERROR: Missing configuration.")
        return

    bot = Bot(token=bot_token)

    # 2. Define Scenario
    # Scenario: User asks for a complex project (expecting referral), then insists on booking.
    history = []

    # Turn 1: User asks about complex bot
    user_input_1 = "Привет! Мне нужен сложный бот для арбитража криптовалют с нейросетями."
    print(f"\n[User]: {user_input_1}")
    history.append({"role": "user", "content": user_input_1})

    response_1 = await llm.generate_response(history)
    print(f"[Bot]: {response_1}")
    history.append({"role": "assistant", "content": response_1})

    # Turn 2: User provides details for booking
    user_input_2 = "Понял. Все равно хочу оставить заявку. Меня зовут Алекс, ник @alex_crypto. Тема: Крипто-бот."
    print(f"\n[User]: {user_input_2}")
    history.append({"role": "user", "content": user_input_2})

    response_2 = await llm.generate_response(history)
    print(f"[Bot]: {response_2}")
    history.append({"role": "assistant", "content": response_2})

    # 3. Check for Summary Block
    summary_match = re.search(r"SUMMARY_BLOCK:\n(.*?)\nEND_SUMMARY_BLOCK", response_2, re.DOTALL)

    if summary_match:
        print("\n[System]: ✅ SUMMARY_BLOCK detected!")
        summary_content = summary_match.group(1).strip()
        print(f"[System]: Parsed Content:\n{summary_content}")

        # 4. Simulate Sending to Admin
        print(f"\n[System]: Sending notification to {admin_id}...")
        try:
            # Simulate the message that handlers.py sends
            user_info = "From: Simulation Script (@jules_test)"
            await bot.send_message(
                chat_id=admin_id,
                text=f"🚀 **Тестовая заявка от Jules**\n(Симуляция беседы)\n\n{user_info}\n\n{summary_content}"
            )
            print("[System]: ✅ Notification sent successfully!")
        except Exception as e:
            print(f"[System]: ❌ Failed to send notification: {e}")
    else:
        print("\n[System]: ⚠️ No SUMMARY_BLOCK generated. Test failed to trigger booking.")

    await bot.session.close()
    print("\n--- SIMULATION COMPLETE ---")

if __name__ == "__main__":
    asyncio.run(simulate_conversation())
