# main.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import BOT_TOKEN, REDIS_URL
from database import engine, Base
from handlers import start, registration
import redis.asyncio as redis

logging.basicConfig(level=logging.INFO)

async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN не задан")

    redis_client = redis.from_url(REDIS_URL)
    storage = RedisStorage(redis_client)

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=storage)

    dp.include_router(start.router)
    dp.include_router(registration.router)

    await on_startup()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
