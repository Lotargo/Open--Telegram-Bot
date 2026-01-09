import os
import re
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
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
    await message.answer(welcome_text)

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

    # Check for SUMMARY_BLOCK
    summary_match = re.search(r"SUMMARY_BLOCK:\n(.*?)\nEND_SUMMARY_BLOCK", response_text, re.DOTALL)

    if summary_match:
        summary_content = summary_match.group(1).strip()
        # Remove the block from the text shown to user to keep it clean,
        # or show it as a confirmation card.
        # Let's show the clean text part first (if any) and then the summary card.

        clean_response = response_text.replace(summary_match.group(0), "").strip()
        if clean_response:
            await message.answer(clean_response)

        # Create approval button
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Все верно, отправить", callback_data="approve_application")]
        ])

        await message.answer(
            f"📋 **Пожалуйста, проверьте данные:**\n\n{summary_content}",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

        # Add assistant response to history (without the block to save space/confusion)
        user_histories[user_id].append({"role": "assistant", "content": clean_response or "Please confirm details."})

    else:
        await message.answer(response_text)
        user_histories[user_id].append({"role": "assistant", "content": response_text})

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
