from aiogram import Router, types, F
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import get_db
from models import UserProgress, CompletedLesson, CompletedExercise, Lesson, Exercise
import datetime

router = Router()

@router.message(F.text == "📊 Прогресс")
async def show_progress(message: types.Message, session: AsyncSession):
    """Показать прогресс пользователя"""
    user_id = message.from_user.id
    
    # Получаем прогресс пользователя
    progress = await session.execute(
        select(UserProgress).where(UserProgress.user_id == user_id)
    )
    progress = progress.scalar_one_or_none()
    
    # Получаем завершенные уроки
    completed_lessons = await session.execute(
        select(CompletedLesson).where(CompletedLesson.user_id == user_id)
    )
    completed_lessons = completed_lessons.scalars().all()
    
    # Получаем завершенные упражнения
    completed_exercises = await session.execute(
        select(CompletedExercise).where(CompletedExercise.user_id == user_id)
    )
    completed_exercises = completed_exercises.scalars().all()
    
    # Формируем текст
    text = "📊 <b>Ваш прогресс в изучении JavaScript</b>\n\n"
    
    if progress:
        # Процент завершенных уроков
        lesson_percentage = 0
        if progress.total_lessons > 0:
            lesson_percentage = int((progress.completed_lessons / progress.total_lessons) * 100)
        
        # Процент завершенных упражнений
        exercise_percentage = 0
        if progress.total_exercises > 0:
            exercise_percentage = int((progress.completed_exercises / progress.total_exercises) * 100)
        
        text += f"📚 <b>Уроки:</b> {progress.completed_lessons}/{progress.total_lessons} ({lesson_percentage}%)\n"
        text += f"✅ <b>Упражнения:</b> {progress.completed_exercises}/{progress.total_exercises} ({exercise_percentage}%)\n"
        text += f"🏆 <b>Очки:</b> {progress.total_points}\n"
        text += f"🔥 <b>Дней подряд:</b> {progress.streak_days}\n"
        text += f"📅 <b>Последняя активность:</b> {progress.last_active.strftime('%d.%m.%Y %H:%M')}\n\n"
    else:
        text += "Вы еще не начали обучение. Начните с первого урока!\n\n"
    
    # Показываем последние завершенные уроки
    if completed_lessons:
        text += "📖 <b>Последние пройденные уроки:</b>\n"
        for i, cl in enumerate(completed_lessons[-3:], 1):  # Последние 3 урока
            lesson = await session.get(Lesson, cl.lesson_id)
            if lesson:
                text += f"{i}. {lesson.title} - {cl.completed_at.strftime('%d.%m.%Y')}\n"
        text += "\n"
    
    # Показываем статистику по упражнениям
    if completed_exercises:
        correct_count = sum(1 for ce in completed_exercises if ce.is_correct)
        total_count = len(completed_exercises)
        accuracy = int((correct_count / total_count) * 100) if total_count > 0 else 0
        
        text += f"🎯 <b>Точность упражнений:</b> {correct_count}/{total_count} ({accuracy}%)\n\n"
    
    # Рекомендации
    text += "💡 <b>Рекомендации:</b>\n"
    
    if not progress or progress.completed_lessons == 0:
        text += "- Начните с первого урока 'Введение в JavaScript'\n"
    elif progress.completed_lessons < 3:
        text += "- Продолжайте изучать базовые уроки\n"
        text += "- Попробуйте выполнить упражнения к пройденным урокам\n"
    else:
        text += "- Отличный прогресс! Рассмотрите уроки средней сложности\n"
        text += "- Практикуйтесь регулярно для закрепления знаний\n"
    
    # Создаем клавиатуру
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📚 Продолжить уроки", callback_data="continue_lessons"),
                InlineKeyboardButton(text="✅ Практика", callback_data="go_practice")
            ],
            [InlineKeyboardButton(text="🔄 Обновить статистику", callback_data="refresh_progress")]
        ]
    )
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "refresh_progress")
async def refresh_progress(callback: types.CallbackQuery, session: AsyncSession):
    """Обновить статистику прогресса"""
    # Пересчитываем прогресс
    user_id = callback.from_user.id
    
    # Считаем завершенные уроки
    completed_lessons_count = await session.execute(
        select(func.count(CompletedLesson.id)).where(CompletedLesson.user_id == user_id)
    )
    completed_lessons_count = completed_lessons_count.scalar()
    
    # Считаем все уроки
    total_lessons_count = await session.execute(
        select(func.count(Lesson.id)).where(Lesson.is_active == True)
    )
    total_lessons_count = total_lessons_count.scalar()
    
    # Считаем завершенные упражнения
    completed_exercises_count = await session.execute(
        select(func.count(CompletedExercise.id)).where(CompletedExercise.user_id == user_id)
    )
    completed_exercises_count = completed_exercises_count.scalar()
    
    # Считаем все упражнения
    total_exercises_count = await session.execute(
        select(func.count(Exercise.id))
    )
    total_exercises_count = total_exercises_count.scalar()
    
    # Считаем очки
    total_points = await session.execute(
        select(func.sum(Exercise.points)).select_from(CompletedExercise)
        .join(Exercise, Exercise.id == CompletedExercise.exercise_id)
        .where(CompletedExercise.user_id == user_id, CompletedExercise.is_correct == True)
    )
    total_points = total_points.scalar() or 0
    
    # Получаем или создаем запись прогресса
    progress = await session.execute(
        select(UserProgress).where(UserProgress.user_id == user_id)
    )
    progress = progress.scalar_one_or_none()
    
    if progress:
        progress.completed_lessons = completed_lessons_count
        progress.total_lessons = total_lessons_count
        progress.completed_exercises = completed_exercises_count
        progress.total_exercises = total_exercises_count
        progress.total_points = total_points
        progress.last_active = datetime.datetime.now()
    else:
        progress = UserProgress(
            user_id=user_id,
            completed_lessons=completed_lessons_count,
            total_lessons=total_lessons_count,
            completed_exercises=completed_exercises_count,
            total_exercises=total_exercises_count,
            total_points=total_points,
            last_active=datetime.datetime.now()
        )
        session.add(progress)
    
    await session.commit()
    
    await callback.answer("Статистика обновлена!")
    
    # Показываем обновленный прогресс
    await show_progress(callback.message, session)


@router.callback_query(F.data == "continue_lessons")
async def continue_lessons(callback: types.CallbackQuery, session: AsyncSession):
    """Продолжить уроки с того места, где остановился пользователь"""
    user_id = callback.from_user.id
    
    # Находим последний завершенный урок
    last_completed = await session.execute(
        select(CompletedLesson).where(CompletedLesson.user_id == user_id)
        .order_by(CompletedLesson.completed_at.desc())
    )
    last_completed = last_completed.scalar_one_or_none()
    
    if last_completed:
        # Находим следующий урок
        next_lesson = await session.execute(
            select(Lesson).where(
                Lesson.order > last_completed.lesson.order,
                Lesson.is_active == True
            ).order_by(Lesson.order).limit(1)
        )
        next_lesson = next_lesson.scalar_one_or_none()
        
        if next_lesson:
            # Показываем следующий урок
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=f"▶️ Начать урок: {next_lesson.title}", callback_data=f"start_lesson_{next_lesson.id}")],
                    [InlineKeyboardButton(text="📚 Все уроки", callback_data="show_all_lessons")]
                ]
            )
            
            await callback.message.edit_text(
                f"📚 <b>Продолжить обучение</b>\n\n"
                f"Вы завершили: <b>{last_completed.lesson.title}</b>\n"
                f"Следующий урок: <b>{next_lesson.title}</b>\n\n"
                f"Хотите начать следующий урок?",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                "🎉 <b>Поздравляем!</b>\n\n"
                "Вы завершили все доступные уроки!\n"
                "Новые уроки скоро появятся.",
                parse_mode="HTML"
            )
    else:
        # Если нет завершенных уроков, предлагаем начать с первого
        first_lesson = await session.execute(
            select(Lesson).where(Lesson.is_active == True).order_by(Lesson.order).limit(1)
        )
        first_lesson = first_lesson.scalar_one_or_none()
        
        if first_lesson:
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=f"▶️ Начать первый урок: {first_lesson.title}", callback_data=f"start_lesson_{first_lesson.id}")]
                ]
            )
            
            await callback.message.edit_text(
                "👋 <b>Добро пожаловать!</b>\n\n"
                "Вы еще не начали обучение.\n"
                "Рекомендуем начать с первого урока:",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                "📚 <b>Уроки</b>\n\n"
                "Пока нет доступных уроков. Скоро добавятся!",
                parse_mode="HTML"
            )
    
    await callback.answer()


@router.callback_query(F.data == "go_practice")
async def go_practice(callback: types.CallbackQuery):
    """Перейти к практике"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Начать практику", callback_data="practice_menu")],
            [InlineKeyboardButton(text="🔙 Назад к прогрессу", callback_data="back_to_progress")]
        ]
    )
    
    await callback.message.edit_text(
        "✅ <b>Практика</b>\n\n"
        "Практические упражнения помогут закрепить знания.\n"
        "Выберите урок для выполнения упражнений:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "show_all_lessons")
async def show_all_lessons(callback: types.CallbackQuery, session: AsyncSession):
    """Показать все уроки"""
    # Имитируем нажатие кнопки "Уроки"
    from handlers.lessons import show_lessons_menu
    await show_lessons_menu(callback.message, session)
    await callback.answer()