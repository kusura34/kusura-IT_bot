from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
import logging


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Message):
            logging.info("Message from %s: %s", event.from_user.id if event.from_user else None, event.text)
        elif isinstance(event, CallbackQuery):
            logging.info("Callback from %s: %s", event.from_user.id if event.from_user else None, event.data)
        return await handler(event, data)
