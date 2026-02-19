from aiogram.fsm.state import State, StatesGroup


class PracticeState(StatesGroup):
    topic_id = State()
    task_id = State()
    waiting_code = State()

@router.callback_query(F.data.startswith("practice_"))
async def start_practice(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    topic_id = int(callback.data.split("_")[1])
    result = await session.execute(
        select(Task).where(Task.topic_id == topic_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        await callback.answer("Для этой темы пока нет практических заданий")
        return

    await state.set_state(PracticeState.topic_id)
    await state.update_data(topic_id=topic_id, task_id=task.id)

    text = f"<b>Практическое задание</b>\n\n{task.description}\n"
    if task.example_input:
        text += f"\nПример ввода: {task.example_input}"
    if task.example_output:
        text += f"\nОжидаемый вывод: {task.example_output}"
    text += "\n\nОтправьте ваш код на JavaScript (одним сообщением)."

    await callback.message.edit_text(text)
    await state.set_state(PracticeState.waiting_code)
    await callback.answer()

@router.message(PracticeState.waiting_code)
async def process_code(message: types.Message, state: FSMContext, session: AsyncSession):
    code = message.text
    if not code:
        await message.answer("Пожалуйста, отправьте код текстом.")
        return

    await message.answer("⏳ Выполняю код...")
    result = await execute_code(code)

    if "error" in result:
        await message.answer(f"❌ Ошибка: {result['error']}")
        return

    output = result.get("stdout", "").strip()
    error = result.get("stderr", "").strip()
    compile_error = result.get("compile", "").strip()

    response = ""
    if output:
        response += f"📤 Вывод:\n<pre>{output}</pre>\n"
    if error:
        response += f"⚠️ Ошибка выполнения:\n<pre>{error}</pre>\n"
    if compile_error:
        response += f"⚙️ Ошибка компиляции:\n<pre>{compile_error}</pre>\n"
    if not response:
        response = "✅ Код выполнен без вывода."

    data = await state.get_data()
    task_id = data['task_id']
    task = await session.get(Task, task_id)
    if task and task.example_output:
        expected = task.example_output.strip()
        if output == expected:
            response += "\n\n🎉 Задание выполнено верно!"
            user_id = message.from_user.id
            topic_id = data['topic_id']
            progress = await session.get(UserProgress, (user_id, topic_id))
            if not progress:
                progress = UserProgress(user_id=user_id, topic_id=topic_id)
            progress.task_completed = True
            await session.commit()
        else:
            response += f"\n\n❌ Ожидалось: <pre>{expected}</pre>"
            response += "\nПопробуйте ещё раз."

    await message.answer(response, parse_mode="HTML")
    await state.clear()
  
class TestState(StatesGroup):
    topic_id = State()
    current_question = State()
    answers = State()
    total = State()

@router.callback_query(F.data.startswith("test_"))
async def start_test(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    topic_id = int(callback.data.split("_")[1])
    # Получаем все вопросы по теме
    result = await session.execute(
        select(Question).where(Question.topic_id == topic_id).order_by(Question.id)
    )
    questions = result.scalars().all()
    if not questions:
        await callback.answer("Для этой темы пока нет тестов")
        return

    await state.set_state(TestState.topic_id)
    await state.update_data(topic_id=topic_id, answers={}, total=len(questions))
    await state.set_state(TestState.current_question)

    await show_question(callback.message, state, session, 0)

async def show_question(message: types.Message, state: FSMContext, session: AsyncSession, index: int):
    data = await state.get_data()
    topic_id = data['topic_id']
    answers = data['answers']
    total = data['total']

    result = await session.execute(
        select(Question).where(Question.topic_id == topic_id).order_by(Question.id)
    )
    questions = result.scalars().all()
    question = questions[index]

    await state.update_data(questions=[q.id for q in questions])

    text = f"Вопрос {index+1}/{total}:\n{question.question_text}"
    kb = question_keyboard(question, index, total)
    await message.edit_text(text, reply_markup=kb)

@router.callback_query(TestState.current_question, F.data.startswith("answer_"))
async def process_answer(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    _, question_id, answer_index = callback.data.split("_")
    question_id = int(question_id)
    answer_index = int(answer_index)

    data = await state.get_data()
    answers = data['answers']
    answers[question_id] = answer_index
    await state.update_data(answers=answers)

    # Получаем вопрос для проверки
    question = await session.get(Question, question_id)
    is_correct = (answer_index == question.correct_option)

    if is_correct:
        await callback.answer("✅ Верно!")
    else:
        correct_text = question.options[question.correct_option]
        await callback.answer(f"❌ Неверно. Правильный ответ: {correct_text}", show_alert=True)

    questions_ids = data.get('questions', [])
    current_index = questions_ids.index(question_id)
    if current_index + 1 < len(questions_ids):
        await show_question(callback.message, state, session, current_index + 1)
    else:
        await finish_test(callback.message, state, session)

@router.callback_query(TestState.current_question, F.data.startswith("prev_"))
async def prev_question(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    _, question_id = callback.data.split("_")
    question_id = int(question_id)
    data = await state.get_data()
    questions_ids = data.get('questions', [])
    current_index = questions_ids.index(question_id)
    if current_index > 0:
        await show_question(callback.message, state, session, current_index - 1)
    else:
        await callback.answer("Это первый вопрос")

@router.callback_query(TestState.current_question, F.data.startswith("next_"))
async def next_question(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    _, question_id = callback.data.split("_")
    question_id = int(question_id)
    data = await state.get_data()
    questions_ids = data.get('questions', [])
    current_index = questions_ids.index(question_id)
    if current_index + 1 < len(questions_ids):
        await show_question(callback.message, state, session, current_index + 1)
    else:
        await callback.answer("Это последний вопрос")

@router.callback_query(TestState.current_question, F.data == "finish_test")
async def finish_test_callback(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    await finish_test(callback.message, state, session)

async def finish_test(message: types.Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    topic_id = data['topic_id']
    answers = data['answers']
    questions_ids = data.get('questions', [])

    result = await session.execute(
        select(Question).where(Question.topic_id == topic_id)
    )
    questions = result.scalars().all()
    correct_count = 0
    total = len(questions)

    user_id = message.from_user.id
    for q in questions:
        answer_idx = answers.get(q.id)
        is_correct = (answer_idx == q.correct_option) if answer_idx is not None else False
        if is_correct:
            correct_count += 1
        user_answer = UserAnswer(
            user_id=user_id,
            question_id=q.id,
            answer_index=answer_idx,
            is_correct=is_correct
        )
        session.add(user_answer)

    progress = await session.get(UserProgress, (user_id, topic_id))
    if not progress:
        progress = UserProgress(user_id=user_id, topic_id=topic_id)
    progress.test_score = correct_count
    progress.completed = True
    progress.completed_at = func.now()
    session.add(progress)
    await session.commit()

    text = f"Тест завершён! Правильных ответов: {correct_count} из {total}"
    await message.edit_text(text, reply_markup=main_menu)
    await state.clear()
