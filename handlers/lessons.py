from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import Lesson, CompletedLesson, UserProgress
from keyboards import lessons_menu, back_to_main_menu
from states import LessonState

router = Router()

@router.message(F.text == "📚 Уроки")
async def show_lessons_menu(message: types.Message, session: AsyncSession):
    """Показать меню уроков"""
    # Получаем уроки, сгруппированные по сложности
    beginner_lessons = await session.execute(
        select(Lesson).where(Lesson.difficulty == "beginner", Lesson.is_active == True).order_by(Lesson.order)
    )
    beginner_lessons = beginner_lessons.scalars().all()
    
    intermediate_lessons = await session.execute(
        select(Lesson).where(Lesson.difficulty == "intermediate", Lesson.is_active == True).order_by(Lesson.order)
    )
    intermediate_lessons = intermediate_lessons.scalars().all()
    
    text = "📚 <b>Доступные уроки</b>\n\n"
    
    if beginner_lessons:
        text += "🌱 <b>Для начинающих:</b>\n"
        for i, lesson in enumerate(beginner_lessons, 1):
            text += f"{i}. {lesson.title}\n"
        text += "\n"
    
    if intermediate_lessons:
        text += "🌿 <b>Для продолжающих:</b>\n"
        for i, lesson in enumerate(intermediate_lessons, 1):
            text += f"{i}. {lesson.title}\n"
    
    if not beginner_lessons and not intermediate_lessons:
        text += "Пока нет доступных уроков. Скоро добавятся!"
    
    await message.answer(text, reply_markup=lessons_menu, parse_mode="HTML")


@router.callback_query(F.data.startswith("lesson_"))
async def select_lesson(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    """Выбор конкретного урока"""
    lesson_id = int(callback.data.split("_")[1])
    
    lesson = await session.get(Lesson, lesson_id)
    if not lesson:
        await callback.answer("Урок не найден")
        return
    
    # Проверяем, пройден ли уже урок
    completed = await session.execute(
        select(CompletedLesson).where(
            CompletedLesson.user_id == callback.from_user.id,
            CompletedLesson.lesson_id == lesson_id
        )
    )
    completed = completed.scalar_one_or_none()
    
    status = "✅ Пройден" if completed else "🆕 Новый"
    
    text = f"""
<b>{lesson.title}</b> {status}

{lesson.description}

📝 <b>Содержание:</b>
{lesson.content[:300]}...

⏱ <b>Время:</b> {lesson.estimated_time} минут
🎯 <b>Сложность:</b> {lesson.difficulty}
"""
    
    # Сохраняем ID урока в состоянии
    await state.update_data(current_lesson_id=lesson_id)
    
    # Создаем клавиатуру с действиями
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    actions_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="▶️ Начать урок", callback_data=f"start_lesson_{lesson_id}")],
            [InlineKeyboardButton(text="📝 Упражнения", callback_data=f"exercises_{lesson_id}")],
            [InlineKeyboardButton(text="🔙 Назад к урокам", callback_data="back_to_lessons")]
        ]
    )
    
    await callback.message.edit_text(text, reply_markup=actions_keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("start_lesson_"))
async def start_lesson(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    """Начать урок"""
    lesson_id = int(callback.data.split("_")[2])
    
    lesson = await session.get(Lesson, lesson_id)
    if not lesson:
        await callback.answer("Урок не найден")
        return
    
    # Устанавливаем состояние урока
    await state.set_state(LessonState.reading)
    await state.update_data(current_lesson_id=lesson_id, current_page=0)
    
    # Разбиваем контент на страницы (условно по 1000 символов)
    content_pages = []
    content = lesson.content
    page_size = 1000
    for i in range(0, len(content), page_size):
        content_pages.append(content[i:i+page_size])
    
    if not content_pages:
        content_pages = [lesson.content]
    
    await state.update_data(content_pages=content_pages, total_pages=len(content_pages))
    
    # Показываем первую страницу
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    page_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️", callback_data="prev_page"),
                InlineKeyboardButton(text=f"1/{len(content_pages)}", callback_data="page_info"),
                InlineKeyboardButton(text="➡️", callback_data="next_page")
            ],
            [InlineKeyboardButton(text="✅ Завершить урок", callback_data=f"complete_lesson_{lesson_id}")]
        ]
    )
    
    await callback.message.edit_text(
        f"<b>{lesson.title}</b>\n\n{content_pages[0]}",
        reply_markup=page_keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "next_page")
async def next_page(callback: types.CallbackQuery, state: FSMContext):
    """Следующая страница урока"""
    data = await state.get_data()
    current_page = data.get("current_page", 0)
    content_pages = data.get("content_pages", [])
    total_pages = data.get("total_pages", 1)
    
    if current_page + 1 >= total_pages:
        await callback.answer("Это последняя страница")
        return
    
    current_page += 1
    await state.update_data(current_page=current_page)
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    page_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️", callback_data="prev_page"),
                InlineKeyboardButton(text=f"{current_page + 1}/{total_pages}", callback_data="page_info"),
                InlineKeyboardButton(text="➡️", callback_data="next_page")
            ],
            [InlineKeyboardButton(text="✅ Завершить урок", callback_data=f"complete_lesson_{data.get('current_lesson_id')}")]
        ]
    )
    
    await callback.message.edit_text(
        f"<b>Страница {current_page + 1}</b>\n\n{content_pages[current_page]}",
        reply_markup=page_keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "prev_page")
async def prev_page(callback: types.CallbackQuery, state: FSMContext):
    """Предыдущая страница урока"""
    data = await state.get_data()
    current_page = data.get("current_page", 0)
    content_pages = data.get("content_pages", [])
    total_pages = data.get("total_pages", 1)
    
    if current_page - 1 < 0:
        await callback.answer("Это первая страница")
        return
    
    current_page -= 1
    await state.update_data(current_page=current_page)
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    page_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️", callback_data="prev_page"),
                InlineKeyboardButton(text=f"{current_page + 1}/{total_pages}", callback_data="page_info"),
                InlineKeyboardButton(text="➡️", callback_data="next_page")
            ],
            [InlineKeyboardButton(text="✅ Завершить урок", callback_data=f"complete_lesson_{data.get('current_lesson_id')}")]
        ]
    )
    
    await callback.message.edit_text(
        f"<b>Страница {current_page + 1}</b>\n\n{content_pages[current_page]}",
        reply_markup=page_keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("complete_lesson_"))
async def complete_lesson(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    """Завершить урок"""
    lesson_id = int(callback.data.split("_")[2])
    
    # Проверяем, не пройден ли уже урок
    existing = await session.execute(
        select(CompletedLesson).where(
            CompletedLesson.user_id == callback.from_user.id,
            CompletedLesson.lesson_id == lesson_id
        )
    )
    existing = existing.scalar_one_or_none()
    
    if existing:
        await callback.answer("Вы уже прошли этот урок")
        return
    
    # Создаем запись о завершении
    completed_lesson = CompletedLesson(
        user_id=callback.from_user.id,
        lesson_id=lesson_id,
        score=100.0
    )
    session.add(completed_lesson)
    
    # Обновляем прогресс пользователя
    progress = await session.execute(
        select(UserProgress).where(UserProgress.user_id == callback.from_user.id)
    )
    progress = progress.scalar_one_or_none()
    
    if progress:
        progress.completed_lessons += 1
        progress.total_points += 10
    else:
        progress = UserProgress(
            user_id=callback.from_user.id,
            completed_lessons=1,
            total_lessons=10,  # временное значение
            total_points=10
        )
        session.add(progress)
    
    await session.commit()
    
    await callback.message.edit_text(
        "🎉 <b>Поздравляем! Вы завершили урок.</b>\n\n"
        "Теперь вы можете перейти к упражнениям или выбрать следующий урок.",
        parse_mode="HTML"
    )
    await callback.answer()
    
    # Очищаем состояние
    await state.clear()