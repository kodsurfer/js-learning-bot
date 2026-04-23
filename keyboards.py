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

lessons_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📖 Список уроков", callback_data="list_lessons")],
        [InlineKeyboardButton(text="▶️ Продолжить обучение", callback_data="continue_learning")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ]
)

practice_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Начать практику", callback_data="start_practice")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="practice_stats")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ]
)

back_to_main_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🏠 В главное меню", callback_data="back_to_main")]
    ]
)
