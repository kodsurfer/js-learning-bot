from aiogram import Router, types
from aiogram.filters import CommandStart
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import User
from keyboards import main_menu

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message, session: AsyncSession):
    user = await session.get(User, message.from_user.id)
    if user:
        await message.answer(
            f"С возвращением, {user.name or 'друг'}!",
            reply_markup=main_menu
        )
    else:
        await message.answer(
            "👋 Привет! Я бот для изучения JavaScript с нуля.\n"
            "Давай познакомимся. Как тебя зовут?"
        )
