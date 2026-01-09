import os
import json
import re
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import CommandStart, Command
from src.llm import LLMClient
from src.database import get_services_context

router = Router()
llm_client = LLMClient()

# In-memory history for MVP: {user_id: [{"role": "...", "content": "..."}]}
user_histories = {}
MAX_HISTORY = 4

@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    user_histories[user_id] = []

    welcome_text = (
        "Привет! Я виртуальный секретарь разработчика.\n"
        "Я могу рассказать о наших услугах, сориентировать по ценам и принять заявку.\n"
        "Спросите меня о чем-нибудь, например: 'Сколько стоит простой бот?'"
    )

    # Request contact button
    contact_kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Отправить контакт", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await message.answer(welcome_text, reply_markup=contact_kb)

@router.message(F.contact)
async def handle_contact(message: Message):
    user_id = message.from_user.id
    contact = message.contact

    # Initialize history if new
    if user_id not in user_histories:
        user_histories[user_id] = []

    # Inject contact info into the conversation history as a system note or user message
    contact_info = f"My contact info: Name={contact.first_name}, Phone={contact.phone_number}"

    # We add this as a 'user' message so the LLM sees the user provided it.
    user_histories[user_id].append({"role": "user", "content": f"[System: User shared contact card]\n{contact_info}"})

    await message.answer(
        "Спасибо! Я сохранил ваш контакт. Чем я могу вам помочь?",
        reply_markup=ReplyKeyboardRemove()
    )

@router.message(Command("set_admin"))
async def cmd_set_admin(message: Message):
    """Helper to get chat ID for config."""
    chat_id = message.chat.id
    await message.answer(
        f"ID этого чата: `{chat_id}`.\n"
        f"Добавьте эту строку в ваш .env файл:\n"
        f"ADMIN_GROUP_ID={chat_id}\n"
        f"Затем перезапустите бота."
    )

@router.message(F.text)
async def handle_message(message: Message):
    user_id = message.from_user.id
    user_text = message.text

    # Initialize history if new
    if user_id not in user_histories:
        user_histories[user_id] = []

    # Update history
    user_histories[user_id].append({"role": "user", "content": user_text})

    # Keep only last N messages to save context/tokens
    if len(user_histories[user_id]) > MAX_HISTORY:
        user_histories[user_id] = user_histories[user_id][-MAX_HISTORY:]

    # Show typing status
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    # Get LLM response
    response_text = await llm_client.generate_response(user_histories[user_id])

    # Try to parse JSON from the response
    booking_data = None
    try:
        # Find JSON block using regex (matches { ... })
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            data = json.loads(json_str)
            if data.get("booking_confirmed"):
                booking_data = data
                # Remove the JSON from the text displayed to the user
                response_text = response_text.replace(json_str, "").strip()
    except Exception as e:
        print(f"JSON Parsing Error: {e}")

    # Send the cleaned response text if there is any (and if it's not just the JSON)
    if response_text:
        await message.answer(response_text)
        user_histories[user_id].append({"role": "assistant", "content": response_text})

    if booking_data:
        # Format the summary for the card
        summary_content = (
            f"Name: {booking_data.get('name', 'Unknown')}\n"
            f"Service: {booking_data.get('service', 'Unknown')}\n"
            f"Topic: {booking_data.get('topic', 'Unknown')}\n"
            f"Contact: {booking_data.get('contact', 'Unknown')}"
        )

        # Create approval button
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Все верно, отправить", callback_data="approve_application")]
        ])

        await message.answer(
            f"📋 **Пожалуйста, проверьте данные:**\n\n{summary_content}",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        # Note: We don't append the summary card itself to history to avoid confusing the LLM with duplicate structured data

@router.callback_query(F.data == "approve_application")
async def approve_application(callback: CallbackQuery, bot: Bot):
    admin_group_id = os.getenv("ADMIN_GROUP_ID")

    if not admin_group_id:
        await callback.answer("Ошибка конфигурации: Админ не настроен.", show_alert=True)
        return

    # Extract summary from the message text
    summary_text = callback.message.text.replace("📋 **Пожалуйста, проверьте данные:**", "").strip()
    user_info = f"From: {callback.from_user.full_name} (@{callback.from_user.username})"

    try:
        await bot.send_message(
            chat_id=admin_group_id,
            text=f"🚀 **Новая заявка!**\n\n{user_info}\n\n{summary_text}"
        )
        await callback.message.edit_text(f"✅ Спасибо! Ваша заявка отправлена.\n\n{summary_text}")
        await callback.answer("Отправлено!")
    except Exception as e:
        print(f"Failed to send to admin: {e}")
        await callback.answer("Ошибка отправки. Попробуйте позже.", show_alert=True)
