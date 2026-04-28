from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any

from services.firebase_client import get_firestore_client
from utils.texts import DEFAULT_TEXTS


class FirestoreService:
    def __init__(self, firebase_credentials: str) -> None:
        self._firebase_credentials = firebase_credentials
        self._db = None

    def _client(self):
        if self._db is None:
            self._db = get_firestore_client(os.getenv("FIREBASE_CREDENTIALS") or self._firebase_credentials)
        return self._db

    async def _run(self, fn, *args, **kwargs):
        return await asyncio.to_thread(fn, *args, **kwargs)

    def _ts(self) -> str:
        return datetime.utcnow().isoformat()

    async def _next_id(self, key: str) -> int:
        db = self._client()
        ref = db.collection("settings").document(f"__counter_{key}")

        @firestore_transactional
        def bump(transaction):
            snap = ref.get(transaction=transaction)
            current = int((snap.to_dict() or {}).get("value", 0)) if snap.exists else 0
            new_value = current + 1
            transaction.set(ref, {"value": new_value}, merge=True)
            return new_value

        transaction = db.transaction()
        return await self._run(bump, transaction)

    async def init(self) -> None:
        await self.seed_defaults()
        await self.seed_faq()
        await self.seed_ready_solutions()

    async def seed_defaults(self) -> None:
        defaults = {
            "contact_telegram": "@your_username",
            "contact_whatsapp": "+1234567890",
            "contact_email": "you@example.com",
            "demo_url": "https://example.com/demo-shop",
            "demo_enabled": "1",
        }
        defaults.update({f"text_{k}": v for k, v in DEFAULT_TEXTS.items()})
        for key, value in defaults.items():
            current = await self.get_setting(key, "")
            if current == "":
                await self.set_setting(key, value)

    async def seed_faq(self) -> None:
        items = await self.list_faq_items()
        if items:
            return
        defaults = [
            ("Сколько занимает разработка?", "Обычно от 5 до 21 дня, в зависимости от объема проекта."),
            ("Сколько стоит сайт?", "Цена зависит от задач. Базовый сайт-визитка стартует от фиксированной минимальной ставки."),
            ("Сколько стоит поддержка Firebase?", "Зависит от объема сопровождения и SLA."),
            ("Как работают Telegram-уведомления?", "События сайта отправляются в webhook, а бот уведомляет мгновенно."),
        ]
        for question, answer in defaults:
            await self.add_faq(question=question, answer=answer)

    async def seed_ready_solutions(self) -> None:
        rows = await self.list_ready_solutions(include_hidden=True)
        if rows:
            return
        defaults = [
            ("Бот для кафе", "Принимает заказы и отправляет на кухню.", "Снижает нагрузку на персонал", "Клиент заказывает из Telegram"),
            ("Бот для записи", "Автоматическая запись клиентов на услуги.", "24/7 запись без администратора", "Салон/студия бронирует слоты"),
            ("Интернет-магазин", "Быстрый запуск онлайн-продаж.", "Каталог + корзина + оплата", "Продажа товаров малого бизнеса"),
            ("CRM для малого бизнеса", "Учет лидов и статусов.", "Контроль заявок и аналитика", "Сервисные компании и агентства"),
        ]
        for idx, item in enumerate(defaults, start=1):
            await self.create_ready_solution(
                title=item[0],
                description=item[1],
                benefits=item[2],
                use_case=item[3],
                sort_order=idx,
            )

    async def create_or_ignore_user(self, user_id: int, username: str | None, full_name: str | None) -> None:
        ref = self._client().collection("users").document(str(user_id))
        snap = await self._run(ref.get)
        if snap.exists:
            return
        await self._run(
            ref.set,
            {
                "id": user_id,
                "username": username or "",
                "full_name": full_name or "",
                "created_at": self._ts(),
            },
        )

    async def get_setting(self, key: str, default: str = "") -> str:
        ref = self._client().collection("settings").document(key)
        snap = await self._run(ref.get)
        if not snap.exists:
            return default
        return str((snap.to_dict() or {}).get("value", default))

    async def set_setting(self, key: str, value: str) -> None:
        ref = self._client().collection("settings").document(key)
        await self._run(ref.set, {"key": key, "value": value}, merge=True)

    async def log_event(self, user_id: int | None, event: str, payload: dict | str | None = None) -> int:
        event_id = await self._next_id("demo_logs")
        value = payload if isinstance(payload, str) else json.dumps(payload or {}, ensure_ascii=False)
        ref = self._client().collection("demo_logs").document(str(event_id))
        await self._run(
            ref.set,
            {"id": event_id, "user_id": user_id, "event": event, "payload": value, "created_at": self._ts()},
        )
        return event_id

    async def count_users(self) -> int:
        docs = await self._run(lambda: list(self._client().collection("users").stream()))
        return len(docs)

    async def count_demo_logs(self, event: str) -> int:
        docs = await self._run(
            lambda: list(self._client().collection("demo_logs").where("event", "==", event).stream())
        )
        return len(docs)

    async def create_project(
        self, *, title: str, description: str, stack: str, image: str, demo_url: str, github_url: str, is_visible: int, sort_order: int
    ) -> int:
        project_id = await self._next_id("projects")
        ref = self._client().collection("projects").document(str(project_id))
        await self._run(
            ref.set,
            {
                "id": project_id,
                "title": title,
                "description": description,
                "stack": stack,
                "image": image,
                "demo_url": demo_url,
                "github_url": github_url,
                "is_visible": int(is_visible),
                "sort_order": int(sort_order),
                "created_at": self._ts(),
            },
        )
        return project_id

    async def list_projects(self, include_hidden: bool = True) -> list[dict[str, Any]]:
        docs = await self._run(lambda: list(self._client().collection("projects").stream()))
        rows = [doc.to_dict() or {} for doc in docs]
        if not include_hidden:
            rows = [r for r in rows if int(r.get("is_visible", 1)) == 1]
        rows.sort(key=lambda r: (int(r.get("sort_order", 100)), -int(r.get("id", 0))))
        return rows

    async def list_project_ids_desc(self) -> list[int]:
        rows = await self.list_projects(include_hidden=True)
        return sorted([int(r["id"]) for r in rows], reverse=True)

    async def get_project(self, project_id: int) -> dict[str, Any] | None:
        ref = self._client().collection("projects").document(str(project_id))
        snap = await self._run(ref.get)
        if not snap.exists:
            return None
        return snap.to_dict() or {}

    async def update_project_fields(self, project_id: int, data: dict[str, Any]) -> None:
        ref = self._client().collection("projects").document(str(project_id))
        await self._run(ref.set, data, merge=True)

    async def delete_project(self, project_id: int) -> None:
        ref = self._client().collection("projects").document(str(project_id))
        await self._run(ref.delete)

    async def get_max_project_sort_order(self) -> int:
        rows = await self.list_projects(include_hidden=True)
        if not rows:
            return 0
        return max(int(r.get("sort_order", 0)) for r in rows)

    async def add_faq(self, *, question: str, answer: str) -> int:
        faq_id = await self._next_id("faq")
        ref = self._client().collection("faq").document(str(faq_id))
        await self._run(ref.set, {"id": faq_id, "question": question, "answer": answer})
        return faq_id

    async def list_faq_items(self) -> list[dict[str, Any]]:
        docs = await self._run(lambda: list(self._client().collection("faq").stream()))
        rows = [doc.to_dict() or {} for doc in docs]
        rows.sort(key=lambda r: int(r.get("id", 0)))
        return rows

    async def get_faq(self, faq_id: int) -> dict[str, Any] | None:
        ref = self._client().collection("faq").document(str(faq_id))
        snap = await self._run(ref.get)
        if not snap.exists:
            return None
        return snap.to_dict() or {}

    async def update_faq(self, faq_id: int, question: str, answer: str) -> None:
        ref = self._client().collection("faq").document(str(faq_id))
        await self._run(ref.set, {"question": question, "answer": answer}, merge=True)

    async def delete_faq(self, faq_id: int) -> None:
        ref = self._client().collection("faq").document(str(faq_id))
        await self._run(ref.delete)

    async def create_ready_solution(self, *, title: str, description: str, benefits: str, use_case: str, sort_order: int) -> int:
        sid = await self._next_id("ready_solutions")
        ref = self._client().collection("ready_solutions").document(str(sid))
        await self._run(
            ref.set,
            {
                "id": sid,
                "title": title,
                "description": description,
                "benefits": benefits,
                "use_case": use_case,
                "is_visible": 1,
                "sort_order": int(sort_order),
                "created_at": self._ts(),
            },
        )
        return sid

    async def list_ready_solutions(self, include_hidden: bool = True) -> list[dict[str, Any]]:
        docs = await self._run(lambda: list(self._client().collection("ready_solutions").stream()))
        rows = [doc.to_dict() or {} for doc in docs]
        if not include_hidden:
            rows = [r for r in rows if int(r.get("is_visible", 1)) == 1]
        rows.sort(key=lambda r: (int(r.get("sort_order", 100)), int(r.get("id", 0))))
        return rows

    async def get_max_ready_solution_sort_order(self) -> int:
        rows = await self.list_ready_solutions(include_hidden=True)
        if not rows:
            return 0
        return max(int(r.get("sort_order", 0)) for r in rows)

    async def update_ready_solution_fields(self, solution_id: int, data: dict[str, Any]) -> None:
        ref = self._client().collection("ready_solutions").document(str(solution_id))
        await self._run(ref.set, data, merge=True)

    async def delete_ready_solution(self, solution_id: int) -> None:
        ref = self._client().collection("ready_solutions").document(str(solution_id))
        await self._run(ref.delete)

    async def list_ready_solution_ids(self) -> list[int]:
        rows = await self.list_ready_solutions(include_hidden=True)
        return [int(r["id"]) for r in rows]

    async def create_lead(
        self, *, user_id: int, project_type: str, payment: str, design: str, admin_panel: str, budget: str, contact: str, tag: str
    ) -> int:
        lead_id = await self._next_id("leads")
        reminder_at = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
        ref = self._client().collection("leads").document(str(lead_id))
        await self._run(
            ref.set,
            {
                "id": lead_id,
                "user_id": user_id,
                "project_type": project_type,
                "payment": payment,
                "design": design,
                "admin_panel": admin_panel,
                "budget": budget,
                "contact": contact,
                "tag": tag,
                "is_processed": 0,
                "reminder_at": reminder_at,
                "reminder_sent": 0,
                "created_at": self._ts(),
            },
        )
        return lead_id

    async def get_lead(self, lead_id: int) -> dict[str, Any] | None:
        ref = self._client().collection("leads").document(str(lead_id))
        snap = await self._run(ref.get)
        if not snap.exists:
            return None
        return snap.to_dict() or {}

    async def list_leads(self, limit: int | None = None) -> list[dict[str, Any]]:
        docs = await self._run(lambda: list(self._client().collection("leads").stream()))
        rows = [doc.to_dict() or {} for doc in docs]
        rows.sort(key=lambda r: int(r.get("id", 0)), reverse=True)
        return rows[:limit] if limit else rows

    async def list_lead_ids(self, limit: int = 60, only_unprocessed: bool = False) -> list[int]:
        rows = await self.list_leads(limit=None)
        if only_unprocessed:
            rows = [r for r in rows if int(r.get("is_processed", 0)) == 0]
        return [int(r["id"]) for r in rows[:limit]]

    async def get_latest_lead_by_user(self, user_id: int) -> dict[str, Any] | None:
        rows = await self.list_leads(limit=None)
        items = [r for r in rows if int(r.get("user_id", 0)) == user_id]
        return items[0] if items else None

    async def mark_lead_processed(self, lead_id: int) -> None:
        ref = self._client().collection("leads").document(str(lead_id))
        await self._run(ref.set, {"is_processed": 1}, merge=True)

    async def mark_lead_reminder_sent(self, lead_id: int) -> None:
        ref = self._client().collection("leads").document(str(lead_id))
        await self._run(ref.set, {"reminder_sent": 1}, merge=True)

    async def delete_lead(self, lead_id: int) -> None:
        ref = self._client().collection("leads").document(str(lead_id))
        await self._run(ref.delete)

    async def list_pending_reminder_leads(self) -> list[dict[str, Any]]:
        rows = await self.list_leads(limit=None)
        return [
            r
            for r in rows
            if int(r.get("is_processed", 0)) == 0 and int(r.get("reminder_sent", 0)) == 0 and bool(r.get("reminder_at"))
        ]


def firestore_transactional(fn):
    from firebase_admin import firestore

    return firestore.transactional(fn)
