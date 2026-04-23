from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json
from database import get_db
from models import Exercise, CompletedExercise, Lesson, UserProgress
from keyboards import practice_menu
from states import PracticeState

router = Router()

@router.message(F.text == "✅ Практика")
async def show_practice_menu(message: types.Message, session: AsyncSession):
    """Показать меню практики"""
    # Получаем уроки, которые пользователь уже начал или завершил
    text = "✅ <b>Практические упражнения</b>\n\n"
    text += "Выберите урок для выполнения упражнений:\n\n"
    
    # Получаем все активные уроки
    lessons = await session.execute(
        select(Lesson).where(Lesson.is_active == True).order_by(Lesson.order)
    )
    lessons = lessons.scalars().all()
    
    if not lessons:
        text += "Пока нет доступных упражнений."
        await message.answer(text, reply_markup=practice_menu, parse_mode="HTML")
        return
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for lesson in lessons:
        # Проверяем количество упражнений в уроке
        exercises_count = await session.execute(
            select(Exercise).where(Exercise.lesson_id == lesson.id)
        )
        exercises_count = len(exercises_count.scalars().all())
        
        # Проверяем, сколько упражнений уже выполнено
        completed_count = await session.execute(
            select(CompletedExercise).where(
                CompletedExercise.user_id == message.from_user.id,
                CompletedExercise.exercise_id.in_(
                    select(Exercise.id).where(Exercise.lesson_id == lesson.id)
                )
            )
        )
        completed_count = len(completed_count.scalars().all())
        
        status = f"({completed_count}/{exercises_count})"
        button_text = f"{lesson.title} {status}"
        
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text=button_text, callback_data=f"practice_lesson_{lesson.id}")
        ])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_main")
    ])
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data.startswith("practice_lesson_"))
async def select_practice_lesson(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    """Выбор урока для практики"""
    lesson_id = int(callback.data.split("_")[2])
    
    lesson = await session.get(Lesson, lesson_id)
    if not lesson:
        await callback.answer("Урок не найден")
        return
    
    # Получаем упражнения для этого урока
    exercises = await session.execute(
        select(Exercise).where(Exercise.lesson_id == lesson_id).order_by(Exercise.id)
    )
    exercises = exercises.scalars().all()
    
    if not exercises:
        await callback.answer("В этом уроке пока нет упражнений")
        return
    
    # Сохраняем информацию в состоянии
    await state.update_data(
        current_lesson_id=lesson_id,
        exercise_ids=[ex.id for ex in exercises],
        current_exercise_index=0,
        user_answers={}
    )
    
    # Начинаем с первого упражнения
    await show_exercise(callback, session, state, exercises[0])
    await callback.answer()


async def show_exercise(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext, exercise: Exercise):
    """Показать упражнение"""
    # Формируем текст упражнения
    text = f"<b>Упражнение</b>\n\n"
    text += f"{exercise.question}\n\n"
    
    if exercise.code_template:
        text += f"<code>{exercise.code_template}</code>\n\n"
    
    # Если это multiple choice, показываем варианты
    if exercise.answer_type == "multiple_choice" and exercise.options:
        try:
            options = json.loads(exercise.options)
            for i, option in enumerate(options, 1):
                text += f"{i}. {option}\n"
        except:
            pass
    
    # Получаем данные состояния
    data = await state.get_data()
    current_index = data.get("current_exercise_index", 0)
    total_exercises = len(data.get("exercise_ids", []))
    
    text += f"\n📊 Прогресс: {current_index + 1}/{total_exercises}"
    
    # Создаем клавиатуру
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    if exercise.answer_type == "multiple_choice" and exercise.options:
        try:
            options = json.loads(exercise.options)
            for i, option in enumerate(options, 1):
                keyboard.inline_keyboard.append([
                    InlineKeyboardButton(text=f"Вариант {i}", callback_data=f"answer_{i}")
                ])
        except:
            pass
    else:
        # Для кодовых упражнений предлагаем ввести ответ
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="✏️ Ввести ответ", callback_data="input_answer")
        ])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="⏭ Пропустить", callback_data="skip_exercise"),
        InlineKeyboardButton(text="🔙 Назад к урокам", callback_data="back_to_practice_menu")
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(PracticeState.answering)


@router.callback_query(F.data == "input_answer")
async def request_answer_input(callback: types.CallbackQuery, state: FSMContext):
    """Запрос ввода ответа"""
    await callback.message.edit_text(
        "Введите ваш ответ (код или текст):\n\n"
        "Вы можете использовать форматирование кода, обернув его в три обратных апострофа:\n"
        "```javascript\n// ваш код\n```",
        parse_mode="HTML"
    )
    await state.set_state(PracticeState.waiting_for_answer)
    await callback.answer()


@router.message(PracticeState.waiting_for_answer)
async def process_answer(message: types.Message, session: AsyncSession, state: FSMContext):
    """Обработка ответа пользователя"""
    data = await state.get_data()
    exercise_ids = data.get("exercise_ids", [])
    current_index = data.get("current_exercise_index", 0)
    
    if current_index >= len(exercise_ids):
        await message.answer("Ошибка: упражнение не найдено")
        await state.clear()
        return
    
    exercise_id = exercise_ids[current_index]
    exercise = await session.get(Exercise, exercise_id)
    
    if not exercise:
        await message.answer("Упражнение не найдено")
        await state.clear()
        return
    
    user_answer = message.text
    
    # Проверяем ответ (упрощенная проверка)
    is_correct = False
    if exercise.answer_type == "code":
        # Для кода просто сравниваем с правильным ответом (упрощенно)
        is_correct = user_answer.strip() == exercise.correct_answer.strip()
    elif exercise.answer_type == "text":
        # Для текста сравниваем без учета регистра
        is_correct = user_answer.lower().strip() == exercise.correct_answer.lower().strip()
    elif exercise.answer_type == "multiple_choice":
        # Для multiple choice ответ уже обработан через callback
        pass
    
    # Сохраняем ответ пользователя
    user_answers = data.get("user_answers", {})
    user_answers[exercise_id] = {
        "answer": user_answer,
        "is_correct": is_correct
    }
    await state.update_data(user_answers=user_answers)
    
    # Создаем запись о выполнении
    completed_exercise = CompletedExercise(
        user_id=message.from_user.id,
        exercise_id=exercise_id,
        user_answer=user_answer,
        is_correct=is_correct,
        attempts=1
    )
    session.add(completed_exercise)
    
    # Обновляем прогресс
    progress = await session.execute(
        select(UserProgress).where(UserProgress.user_id == message.from_user.id)
    )
    progress = progress.scalar_one_or_none()
    
    if progress:
        progress.completed_exercises += 1
        if is_correct:
            progress.total_points += exercise.points
    else:
        progress = UserProgress(
            user_id=message.from_user.id,
            completed_exercises=1,
            total_exercises=len(exercise_ids),
            total_points=exercise.points if is_correct else 0
        )
        session.add(progress)
    
    await session.commit()
    
    # Показываем результат
    result_text = "✅ <b>Правильно!</b>" if is_correct else "❌ <b>Неправильно</b>"
    if exercise.explanation:
        result_text += f"\n\n💡 <b>Объяснение:</b>\n{exercise.explanation}"
    
    result_text += "\n\nНажмите 'Далее' для перехода к следующему упражнению."
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➡️ Далее", callback_data="next_exercise")]
        ]
    )
    
    await message.answer(result_text, reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(PracticeState.answering)


@router.callback_query(F.data.startswith("answer_"))
async def process_multiple_choice(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    """Обработка выбора варианта в multiple choice"""
    selected_option = int(callback.data.split("_")[1]) - 1  # 0-based index
    
    data = await state.get_data()
    exercise_ids = data.get("exercise_ids", [])
    current_index = data.get("current_exercise_index", 0)
    
    if current_index >= len(exercise_ids):
        await callback.answer("Ошибка: упражнение не найдено")
        await state.clear()
        return
    
    exercise_id = exercise_ids[current_index]
    exercise = await session.get(Exercise, exercise_id)
    
    if not exercise or exercise.answer_type != "multiple_choice":
        await callback.answer("Ошибка формата упражнения")
        return
    
    # Получаем правильный ответ
    try:
        options = json.loads(exercise.options)
        correct_index = int(exercise.correct_answer) - 1  # предполагаем, что correct_answer хранит номер правильного варианта
        is_correct = selected_option == correct_index
    except:
        is_correct = False
    
    # Сохраняем ответ
    user_answers = data.get("user_answers", {})
    user_answers[exercise_id] = {
        "answer": str(selected_option + 1),
        "is_correct": is_correct
    }
    await state.update_data(user_answers=user_answers)
    
    # Создаем запись о выполнении
    completed_exercise = CompletedExercise(
        user_id=callback.from_user.id,
        exercise_id=exercise_id,
        user_answer=str(selected_option + 1),
        is_correct=is_correct,
        attempts=1
    )
    session.add(completed_exercise)
    
    # Обновляем прогресс
    progress = await session.execute(
        select(UserProgress).where(UserProgress.user_id == callback.from_user.id)
    )
    progress = progress.scalar_one_or_none()
    
    if progress:
        progress.completed_exercises += 1
        if is_correct:
            progress.total_points += exercise.points
    else:
        progress = UserProgress(
            user_id=callback.from_user.id,
            completed_exercises=1,
            total_exercises=len(exercise_ids),
            total_points=exercise.points if is_correct else 0
        )
        session.add(progress)
    
    await session.commit()
    
    # Показываем результат
    result_text = "✅ <b>Правильно!</b>" if is_correct else "❌ <b>Неправильно</b>"
    if exercise.explanation:
        result_text += f"\n\n💡 <b>Объяснение:</b>\n{exercise.explanation}"
    
    result_text += "\n\nНажмите 'Далее' для перехода к следующему упражнению."
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➡️ Далее", callback_data="next_exercise")]
        ]
    )
    
    await callback.message.edit_text(result_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "next_exercise")
async def next_exercise(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    """Переход к следующему упражнению"""
    data = await state.get_data()
    exercise_ids = data.get("exercise_ids", [])
    current_index = data.get("current_exercise_index", 0)
    
    if current_index + 1 >= len(exercise_ids):
        # Все упражнения пройдены
        await show_practice_summary(callback, session, state)
        return
    
    # Переходим к следующему упражнению
    current_index += 1
    await state.update_data(current_exercise_index=current_index)
    
    next_exercise_id = exercise_ids[current_index]
    next_exercise = await session.get(Exercise, next_exercise_id)
    
    if not next_exercise:
        await callback.answer("Ошибка: упражнение не найдено")
        return
    
    await show_exercise(callback, session, state, next_exercise)
    await callback.answer()


@router.callback_query(F.data == "skip_exercise")
async def skip_exercise(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    """Пропуск упражнения"""
    data = await state.get_data()
    exercise_ids = data.get("exercise_ids", [])
    current_index = data.get("current_exercise_index", 0)
    
    if current_index + 1 >= len(exercise_ids):
        # Все упражнения пройдены
        await show_practice_summary(callback, session, state)
        return
    
    # Пропускаем текущее упражнение
    current_index += 1
    await state.update_data(current_exercise_index=current_index)
    
    next_exercise_id = exercise_ids[current_index]
    next_exercise = await session.get(Exercise, next_exercise_id)
    
    if not next_exercise:
        await callback.answer("Ошибка: упражнение не найдено")
        return
    
    await show_exercise(callback, session, state, next_exercise)
    await callback.answer()


async def show_practice_summary(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    """Показать итоги практики"""
    data = await state.get_data()
    user_answers = data.get("user_answers", {})
    exercise_ids = data.get("exercise_ids", [])
    
    correct_count = sum(1 for answer in user_answers.values() if answer.get("is_correct"))
    total_count = len(exercise_ids)
    
    text = f"🎉 <b>Практика завершена!</b>\n\n"
    text += f"📊 <b>Результаты:</b>\n"
    text += f"✅ Правильных ответов: {correct_count}/{total_count}\n"
    text += f"📈 Процент успеха: {int(correct_count / total_count * 100) if total_count > 0 else 0}%\n\n"
    
    if correct_count == total_count:
        text += "🏆 Отличная работа! Вы справились со всеми заданиями!"
    elif correct_count >= total_count * 0.7:
        text += "👍 Хороший результат! Продолжайте в том же духе!"
    else:
        text += "💪 Не расстраивайтесь! Практика делает мастера. Попробуйте еще раз!"
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 К меню практики", callback_data="back_to_practice_menu")],
            [InlineKeyboardButton(text="🏠 В главное меню", callback_data="back_to_main")]
        ]
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await state.clear()