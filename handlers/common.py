from aiogram import Router
from aiogram.types import ErrorEvent
import logging

router = Router()


@router.errors()
async def errors_handler(event: ErrorEvent):
    logging.exception("Unhandled update error", exc_info=event.exception)
    if event.update.message:
        await event.update.message.answer("Произошла ошибка. Попробуйте еще раз чуть позже.")
    elif event.update.callback_query:
        await event.update.callback_query.answer("Ошибка. Повторите позже.", show_alert=True)
    return True
