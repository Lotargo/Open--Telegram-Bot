import os
import json
import re
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from src.llm import LLMClient
from src.database import get_services_context, save_user, get_user, delete_user
from src.prompts import set_mode, list_modes, get_current_mode

router = Router()
llm_client = LLMClient()

# In-memory history for MVP: {user_id: [{"role": "...", "content": "..."}]}
user_histories = {}
MAX_HISTORY = 4

class FeedbackState(StatesGroup):
    waiting_for_message = State()

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Отправить контакт", request_contact=True)],
            [KeyboardButton(text="❓ FAQ"), KeyboardButton(text="ℹ️ О нас")],
            [KeyboardButton(text="👤 Мой профиль"), KeyboardButton(text="📩 Обратная связь")]
        ],
        resize_keyboard=True
    )

@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    user_histories[user_id] = []

    welcome_text = (
        "Привет! Я виртуальный секретарь разработчика.\n"
        "Я могу рассказать о наших услугах, сориентировать по ценам и принять заявку.\n"
        "Используйте кнопки меню для навигации или просто напишите ваш вопрос."
    )

    await message.answer(welcome_text, reply_markup=get_main_keyboard())

@router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "🤖 **Список команд:**\n\n"
        "/start - Перезапустить бота\n"
        "/clear - Очистить историю диалога\n"
        "/profile - Мой профиль\n"
        "/feedback - Написать разработчику\n"
        "/help - Показать это сообщение"
    )
    await message.answer(help_text, parse_mode="Markdown")

@router.message(Command("clear"))
async def cmd_clear(message: Message):
    user_id = message.from_user.id
    user_histories[user_id] = []
    await message.answer("🧹 История диалога очищена.")

@router.message(Command("profile"))
async def cmd_profile(message: Message):
    user_id = message.from_user.id
    user_data = get_user(user_id)

    if not user_data:
        await message.answer("❌ У меня нет ваших сохраненных данных.")
        return

    profile_text = (
        f"👤 **Ваш профиль:**\n"
        f"Имя: {user_data.get('name')}\n"
        f"Телефон: {user_data.get('phone')}"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Удалить мои данные", callback_data="delete_my_data")]
    ])

    await message.answer(profile_text, reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data == "delete_my_data")
async def handle_delete_data(callback: CallbackQuery):
    user_id = callback.from_user.id
    if delete_user(user_id):
        await callback.message.edit_text("✅ Ваши данные были успешно удалены из базы.")
    else:
        await callback.message.edit_text("❌ Ошибка удаления или данные не найдены.")

@router.message(F.text == "👤 Мой профиль")
async def text_profile(message: Message):
    await cmd_profile(message)

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Admin help command."""
    await message.answer(
        "🛠 **Панель администратора:**\n\n"
        "/set_mode <mode> - Сменить режим бота\n"
        "/modes - Список доступных режимов\n"
        "/set_admin - Узнать ID чата для конфига"
    )

@router.message(Command("modes"))
async def cmd_modes(message: Message):
    modes = list_modes()
    current = get_current_mode()
    text = f"Текущий режим: **{current}**\n\nДоступные режимы:\n" + "\n".join([f"- {m}" for m in modes])
    await message.answer(text, parse_mode="Markdown")

@router.message(Command("set_mode"))
async def cmd_set_mode(message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Использование: /set_mode <mode_name>")
        return

    mode_name = args[1]
    if set_mode(mode_name):
        await message.answer(f"✅ Режим бота изменен на: **{mode_name}**", parse_mode="Markdown")
    else:
        await message.answer(f"❌ Режим `{mode_name}` не найден. Проверьте папку config/prompts.", parse_mode="Markdown")

@router.message(F.text == "ℹ️ О нас")
async def handle_about(message: Message):
    about_text = (
        "👨‍💻 **О нас**\n\n"
        "Мы команда разработчиков, специализирующаяся на создании чат-ботов, веб-сервисов и автоматизации бизнеса.\n"
        "Наш стек: Python, MongoDB, Docker, LLM (GPT/Llama)."
    )
    await message.answer(about_text, parse_mode="Markdown")

# --- FAQ Handling ---
@router.message(F.text == "❓ FAQ")
async def handle_faq_button(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Цены", callback_data="faq_prices")],
        [InlineKeyboardButton(text="⏳ Сроки", callback_data="faq_timeline")],
        [InlineKeyboardButton(text="📞 Контакты", callback_data="faq_contacts")]
    ])
    await message.answer("Выберите тему:", reply_markup=kb)

@router.callback_query(F.data.startswith("faq_"))
async def handle_faq_callback(callback: CallbackQuery):
    topic = callback.data.split("_")[1]
    text = ""
    if topic == "prices":
        text = "💰 **Цены:**\n- Простой бот: $100-$300\n- Сложный бот: от $500\n- Консультация: $50/час"
    elif topic == "timeline":
        text = "⏳ **Сроки:**\n- Простой бот: 3-5 дней\n- Сложный проект: 2+ недели"
    elif topic == "contacts":
        text = "📞 **Контакты:**\nПишите @Lotargo для обсуждения деталей."

    await callback.message.edit_text(text, parse_mode="Markdown")
    await callback.answer()

# --- Feedback Handling ---
@router.message(Command("feedback"))
@router.message(F.text == "📩 Обратная связь")
async def cmd_feedback(message: Message, state: FSMContext):
    await message.answer("✍️ Напишите ваше сообщение, и я передам его администратору.")
    await state.set_state(FeedbackState.waiting_for_message)

@router.message(FeedbackState.waiting_for_message)
async def process_feedback(message: Message, state: FSMContext, bot: Bot):
    admin_group_id = os.getenv("ADMIN_GROUP_ID")
    if not admin_group_id:
        await message.answer("❌ Ошибка: Админ не настроен.")
        await state.clear()
        return

    user_info = f"Feedback from: {message.from_user.full_name} (@{message.from_user.username})"
    try:
        await bot.send_message(
            chat_id=admin_group_id,
            text=f"📩 **Новое сообщение!**\n\n{user_info}\n\n{message.text}"
        )
        await message.answer("✅ Сообщение отправлено! Мы свяжемся с вами.")
    except Exception as e:
        print(f"Failed to send feedback: {e}")
        await message.answer("❌ Ошибка отправки.")

    await state.clear()

@router.message(F.contact)
async def handle_contact(message: Message):
    user_id = message.from_user.id
    contact = message.contact

    # Persist contact info
    user_data = {
        "user_id": user_id,
        "name": f"{contact.first_name} {contact.last_name or ''}".strip(),
        "phone": contact.phone_number
    }
    save_user(user_id, user_data)

    # Initialize history if new
    if user_id not in user_histories:
        user_histories[user_id] = []

    # Inject contact info into the conversation history as a system note or user message
    contact_info = f"My contact info: Name={user_data['name']}, Phone={user_data['phone']}"

    # We add this as a 'user' message so the LLM sees the user provided it.
    user_histories[user_id].append({"role": "user", "content": f"[System: User shared contact card]\n{contact_info}"})

    await message.answer(
        "Спасибо! Я сохранил ваш контакт. Чем я могу вам помочь?",
        reply_markup=get_main_keyboard()
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

    # Inject persistent contact info into LLM context if available (invisible to user, but visible to LLM)
    history_for_llm = list(user_histories[user_id])
    user_data = get_user(user_id)
    if user_data:
        # Prepend or append a system note ensuring the LLM knows the contact
        # Adding it as the first message in the history being sent effectively reminds the LLM
        contact_note = (
            f"[System Note: The user's verified contact details are:\n"
            f"Name: {user_data.get('name')}\n"
            f"Phone: {user_data.get('phone')}\n"
            f"Please use these details when filling out the booking form if needed.]"
        )
        # We insert it at the beginning of the history sent to LLM (after system prompt)
        # Note: LLMClient.generate_response takes history. We can modify the history passed.
        # However, `generate_response` prepends the system prompt.
        # Let's just prepend it to the history list passed to the function.
        history_for_llm.insert(0, {"role": "system", "content": contact_note})


    # Get LLM response
    response_text = await llm_client.generate_response(history_for_llm)

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
        # Fallback/Merge with known contact info if LLM missed it or returned placeholders
        llm_name = booking_data.get('name', '')
        llm_contact = booking_data.get('contact', '')

        # Heuristic: if LLM returns "Unknown" or "Пользователь" or empty, override with known info
        is_generic_name = not llm_name or llm_name.lower() in ['unknown', 'пользователь', 'user', 'unknown user']
        is_generic_contact = not llm_contact or llm_contact.lower() in ['unknown', 'пользователь', 'user', 'unknown user']

        real_name = llm_name
        real_contact = llm_contact

        user_data = get_user(user_id)
        if user_data:
            if is_generic_name:
                real_name = user_data.get('name', real_name)
            if is_generic_contact:
                real_contact = user_data.get('phone', real_contact)

        # Format the summary for the card
        summary_content = (
            f"Name: {real_name}\n"
            f"Service: {booking_data.get('service', 'Unknown')}\n"
            f"Topic: {booking_data.get('topic', 'Unknown')}\n"
            f"Contact: {real_contact}"
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
