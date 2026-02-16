from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from models import User
from states import Registration
from keyboards import level_keyboard, skip_goal_keyboard, main_menu

router = Router()

@router.message(Registration.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(
        "Выбери свой уровень подготовки:",
        reply_markup=level_keyboard
    )
    await state.set_state(Registration.level)

@router.callback_query(Registration.level, F.data.startswith("level_"))
async def process_level(callback: types.CallbackQuery, state: FSMContext):
    level = callback.data.split("_")[1]
    await state.update_data(level=level)
    await callback.message.edit_text(
        "Какая у тебя цель обучения? (например, 'стать веб-разработчиком')\n"
        "Или нажми 'Пропустить'.",
        reply_markup=skip_goal_keyboard
    )
    await state.set_state(Registration.goal)

@router.callback_query(Registration.goal, F.data == "skip_goal")
async def skip_goal(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    await finish_registration(callback.message, state, session, goal=None)
    await callback.answer()

@router.message(Registration.goal)
async def process_goal(message: types.Message, state: FSMContext, session: AsyncSession):
    await finish_registration(message, state, session, goal=message.text)

async def finish_registration(event: types.Message, state: FSMContext, session: AsyncSession, goal):
    data = await state.get_data()
    name = data.get("name")
    level = data.get("level")

    new_user = User(
        telegram_id=event.from_user.id,
        name=name,
        level=level,
        goal=goal
    )
    session.add(new_user)
    await session.commit()

    await event.answer(
        f"Отлично, {name}! Регистрация завершена.\n"
        "Теперь ты можешь приступить к урокам.",
        reply_markup=main_menu
    )
    await state.clear()
  
