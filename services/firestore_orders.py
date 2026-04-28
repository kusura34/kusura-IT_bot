from __future__ import annotations

import asyncio
import logging
import os
import threading
import time
from typing import Any

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from services.firebase_client import get_firestore_client


LOGGER = logging.getLogger(__name__)


def _safe_value(data: dict[str, Any], *keys: str, default: str = "Не указано") -> str:
    for key in keys:
        value = data.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return default


class FirestoreOrdersListener:
    def __init__(self, *, bot: Bot, admin_id: int, event_loop: asyncio.AbstractEventLoop, firebase_credentials: str) -> None:
        self._bot = bot
        self._admin_id = admin_id
        self._event_loop = event_loop
        self._firebase_credentials = firebase_credentials
        self._db = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._watch = None
        self._seen_doc_ids: set[str] = set()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._seen_doc_ids.clear()
        self._thread = threading.Thread(target=self._watch_orders, name="firestore-orders-listener", daemon=True)
        self._thread.start()
        LOGGER.info("Firestore listener thread started")

    def stop(self) -> None:
        self._stop_event.set()
        if self._watch:
            self._watch.unsubscribe()
            self._watch = None
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)

    def _init_firestore(self) -> None:
        self._db = get_firestore_client(os.getenv("FIREBASE_CREDENTIALS") or self._firebase_credentials)

    def _watch_orders(self) -> None:
        try:
            self._init_firestore()
            self._watch = self._db.collection("orders").on_snapshot(self._on_snapshot)
            LOGGER.info("Firestore on_snapshot listener attached to 'orders'")

            while not self._stop_event.is_set():
                time.sleep(1)
        except Exception:
            LOGGER.exception("Failed to start Firestore orders listener")

    def _on_snapshot(self, collection_snapshot, changes, read_time) -> None:
        del collection_snapshot, read_time
        for change in changes:
            if change.type.name != "ADDED":
                continue
            doc_id = change.document.id
            order_data = change.document.to_dict() or {}
            if bool(order_data.get("is_processed")):
                continue
            if doc_id in self._seen_doc_ids:
                continue
            self._seen_doc_ids.add(doc_id)
            future = asyncio.run_coroutine_threadsafe(
                self._notify_admin_about_new_order(doc_id=doc_id, order_data=order_data),
                self._event_loop,
            )
            future.add_done_callback(self._handle_future_result)

    @staticmethod
    def _handle_future_result(future: "asyncio.Future[Any]") -> None:
        try:
            future.result()
        except Exception:
            LOGGER.exception("Failed to send Firestore order notification")

    async def _notify_admin_about_new_order(self, *, doc_id: str, order_data: dict[str, Any]) -> None:
        client_name = _safe_value(order_data, "client_name", "name", "customer_name")
        phone = _safe_value(order_data, "phone", "phone_number", "contact")
        site_type = _safe_value(order_data, "site_type", "website_type", "type")

        text = (
            "🔥 <b>Новый заказ из Firestore</b>\n"
            f"ID: <code>{doc_id}</code>\n"
            f"Клиент: {client_name}\n"
            f"Телефон: {phone}\n"
            f"Тип сайта: {site_type}"
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Обработано", callback_data=f"fire:order:process:{doc_id}"),
                    InlineKeyboardButton(text="🗑 Удалить", callback_data=f"fire:order:delete:{doc_id}"),
                ]
            ]
        )

        await self._bot.send_message(chat_id=self._admin_id, text=text, reply_markup=keyboard)
