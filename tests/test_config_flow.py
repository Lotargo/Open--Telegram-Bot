import asyncio
import os
import re
import json
from dotenv import load_dotenv
from aiogram import Bot

# Manually add src to path to import modules
import sys
sys.path.append(os.path.join(os.getcwd(), ''))

from src.llm import LLMClient
from src.config import LLM_CONFIG

# Load env vars
load_dotenv()

async def simulate_conversation():
    print("--- STARTING JSON FLOW TEST ---\n")

    # 2. Initialize Components
    llm = LLMClient()
    bot_token = os.getenv("BOT_TOKEN")

    # 3. Define Scenario
    # Scenario: User shares contact, then books with Topic.
    history = []

    # Turn 1: User shares contact
    print(f"\n[User Action]: Shared Contact (Phone: +1234567890)")
    history.append({"role": "user", "content": "[System: User shared contact card]\nMy contact info: Name=Alex, Phone=+1234567890"})

    # Turn 2: User asks to book with Topic
    user_input = "Меня зовут Алекс. Хочу заказать простого бота для магазина кроссовок. Подтверждаю."
    print(f"\n[User]: {user_input}")
    history.append({"role": "user", "content": user_input})

    response = await llm.generate_response(history)
    print(f"[Bot Raw Output]: {response}")

    # 4. Check for JSON Block
    booking_data = None
    json_match = re.search(r"\{.*\}", response, re.DOTALL)

    if json_match:
        try:
            data = json.loads(json_match.group(0))
            if data.get("booking_confirmed"):
                booking_data = data
                print("\n[System]: ✅ JSON Booking Confirmed!")
                print(f"[System]: Data: {json.dumps(data, indent=2, ensure_ascii=False)}")

                if "+1234567890" in str(data):
                    print("[System]: ✅ Contact Phone correctly extracted!")
                else:
                    print("[System]: ⚠️ Contact Phone NOT found in JSON.")
            else:
                 print("\n[System]: ⚠️ JSON found but booking_confirmed is False/Missing.")
        except json.JSONDecodeError:
            print("\n[System]: ❌ JSON Decode Error.")
    else:
        print("\n[System]: ⚠️ No JSON block found.")

    print("\n--- TEST COMPLETE ---")

if __name__ == "__main__":
    asyncio.run(simulate_conversation())
