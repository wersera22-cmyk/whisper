import hashlib
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8666834209:AAFgc4r5X8Vo4_gMXfX92OuNPcMJfJCtNtI"
bot = Bot(token=TOKEN)
dp = Dispatcher()
whispers = {}
@dp.inline_query()
async def inline_handler(query: types.InlineQuery):
    text = query.query
    if not text:
        return

    # Находим ВСЕ упоминания @username или ID в тексте
    recipients = re.findall(r'(@\w+|[0-9]{5,15})', text)
    targets = recipients[:5]

    # Очищаем текст сообщения от упоминаний получателей
    clean_text = text
    for r in targets:
        clean_text = clean_text.replace(r, "")
    clean_text = clean_text.strip()

    if targets:
        recipients_str = ", ".join(targets)
        title = f"🤫 Шёпот для {recipients_str}"
        preview = f"🔒 Секретное сообщение для {recipients_str}. Только он может прочитать содержимое."
    else:
        title = "🤫 Шёпот для всех"
        preview = "📩 Секретное сообщение для всех!(каждый может увидеть содержимое.📌"

    w_id = hashlib.md5(text.encode()).hexdigest()
    whispers[w_id] = {
        "text": clean_text,
        "allowed": targets,
        "author_id": query.from_user.id
    }

    btn = InlineKeyboardButton(text="Посмотреть содержимое 🔍", callback_data=f"wh_{w_id}")
    kb = InlineKeyboardMarkup(inline_keyboard=[[btn]])
    content = InputTextMessageContent(message_text=preview)

    item = InlineQueryResultArticle(
        id=w_id,
        title=title,
        description=f"Текст: {clean_text[:30]}...",
        input_message_content=content,
        reply_markup=kb
    )

    await query.answer(results=[item], cache_time=1)


@dp.callback_query(F.data.startswith("wh_"))
async def read_whisper(call: types.CallbackQuery):
    w_id = call.data.replace("wh_", "")

    if w_id in whispers:
        data = whispers[w_id]
        user_id = str(call.from_user.id)
        user_name = f"@{call.from_user.username}" if call.from_user.username else None

        is_allowed = (
                not data["allowed"] or
                call.from_user.id == data["author_id"] or
                user_id in data["allowed"] or
                (user_name and user_name in data["allowed"])
        )

        if is_allowed:
            await call.answer(data["text"], show_alert=True)
        else:
            await call.answer("🔒 Извините, но этот шёпот предназначен не вам!", show_alert=True)
    else:
        await call.answer("❌ Сообщение не найдено.", show_alert=True)


@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    me = await bot.get_me()
    text = (
        "👋 Привет! Я бот для секретных сообщений.\n\n"
        "1️⃣ Как отправить шёпот?\n"
        f"В любом чате напиши: @{me.username} Текст @user1 @user2.\n"
        "Только указанные люди смогут его прочитать.\n\n"
        "2️⃣ Как узнать ID?\n"
        "Просто перешли мне любое сообщение."
    )
    await message.answer(text, parse_mode="Markdown")


@dp.message()
async def forward_handler(message: types.Message):
    if message.forward_date:
        if message.forward_from:
            user = message.forward_from
            # Добавили  вокург {user.id}
            await message.answer(f"👤 Юзер: @{user.username or 'нет'}\n🆔 ID: {user.id}", parse_mode="Markdown")
        elif message.forward_from_chat:
            chat = message.forward_from_chat
            # Добавили  вокруг {chat.id}
            await message.answer(f"📢 Источник: {chat.title}\n🆔 ID: {chat.id}", parse_mode="Markdown")
        else:
            await message.answer(
                "⚠️ Упс! Информация скрыта.\n\n"
                "Этот пользователь ограничил доступ к своему аккаунту при пересылке сообщений. "
                "Я не могу узнать его ID.",
                parse_mode="Markdown"
            )

if __name__ == "__main__":
            print("Бот запущен. Приватность и проверка скрытых профилей работают!")
            dp.run_polling(bot)