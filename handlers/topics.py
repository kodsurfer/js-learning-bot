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
  
