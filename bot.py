import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

import config
import database as db
from handlers import start, channel, posts, payments, account
from webhook_server import create_app
from aiohttp import web

logging.basicConfig(level=logging.INFO)


async def run_webhook_server():
    """Click/Payme callbacklarini qabul qiluvchi aiohttp serverni parallel ishga tushiradi.
    Agar port band bo'lsa yoki boshqa xatolik yuz bersa, botning o'zi (polling) baribir
    ishlashda davom etadi — faqat ogohlantirish chiqadi."""
    try:
        app = create_app()
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, config.WEBHOOK_HOST, config.WEBHOOK_PORT)
        await site.start()
        logging.info(f"Webhook server {config.WEBHOOK_HOST}:{config.WEBHOOK_PORT} da ishga tushdi")
    except Exception as e:
        logging.warning(
            f"Webhook/Mini-App server ishga tushmadi ({e}). "
            "Bot (Telegram polling) baribir ishlayveradi, lekin Mini App va "
            "Click/Payme callbacklari ishlamaydi."
        )


async def main():
    await db.init_db()

    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start.router)
    dp.include_router(channel.router)
    dp.include_router(posts.router)
    dp.include_router(payments.router)
    dp.include_router(account.router)

    await run_webhook_server()

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
