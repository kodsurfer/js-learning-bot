from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📚 Уроки")],
        [KeyboardButton(text="✅ Практика")],
        [KeyboardButton(text="📊 Прогресс")],
        [KeyboardButton(text="⚙️ Настройки")]
    ],
    resize_keyboard=True
)

level_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🌱 Полный новичок", callback_data="level_beginner")],
        [InlineKeyboardButton(text="🌿 Есть базовые знания", callback_data="level_intermediate")]
    ]
)

skip_goal_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="⏭ Пропустить", callback_data="skip_goal")]
    ]
)
