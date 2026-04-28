import asyncio
import logging

from aiohttp import web
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import load_config
from handlers import admin, brief, common, contact, demo, faq, navigation, portfolio, start
from services.firestore_service import FirestoreService
from middlewares.logging import LoggingMiddleware
from services.firestore_orders import FirestoreOrdersListener
from services.scheduler import ReminderScheduler


async def run_demo_webhook_server(bot: Bot, db: FirestoreService, host: str, port: int):
    app = web.Application()
    app["bot"] = bot
    app["db"] = db
    app.add_routes([web.post("/demo-webhook", demo.demo_webhook)])

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=host, port=port)
    await site.start()
    logging.info("Demo webhook server started on http://%s:%s/demo-webhook", host, port)
    return runner


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

    config = load_config()
    db = FirestoreService(config.firebase_credentials)
    await db.init()

    bot = Bot(token=config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.start()
    reminder_scheduler = ReminderScheduler(scheduler=scheduler, bot=bot, db=db)
    await reminder_scheduler.restore_jobs()

    dp.update.middleware(LoggingMiddleware())

    dp["config"] = config
    dp["db"] = db
    dp["reminder_scheduler"] = reminder_scheduler

    dp.include_router(common.router)
    dp.include_router(start.router)
    dp.include_router(navigation.router)
    dp.include_router(portfolio.router)
    dp.include_router(brief.router)
    dp.include_router(demo.router)
    dp.include_router(faq.router)
    dp.include_router(contact.router)
    dp.include_router(admin.router)

    firestore_listener = FirestoreOrdersListener(
        bot=bot,
        admin_id=config.admin_id,
        event_loop=asyncio.get_running_loop(),
        firebase_credentials=config.firebase_credentials,
    )
    firestore_listener.start()

    webhook_runner = await run_demo_webhook_server(bot=bot, db=db, host=config.webhook_host, port=config.webhook_port)

    try:
        await dp.start_polling(bot)
    finally:
        firestore_listener.stop()
        scheduler.shutdown(wait=False)
        await webhook_runner.cleanup()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
