import asyncio
import os
from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from keyboards.brief import budget_keyboard, post_brief_keyboard, project_type_keyboard, yes_no_keyboard
from keyboards.navigation import back_home_keyboard
from services.firebase_client import get_firestore_client
from services.notifier import notify_admin_new_lead
from states.brief import BriefStates

router = Router()

COOLDOWN_MINUTES = 10


def normalize_yes_no(value: str) -> str:
    return "Да" if value == "yes" else "Нет"


def detect_tag(project_type: str, budget: str) -> str:
    if budget == "1000$+" or project_type in {"Маркетплейс", "Интернет-магазин"}:
        return "горячий"
    if budget == "300–1000$":
        return "средний"
    return "холодный"


@router.callback_query(F.data == "menu:brief")
async def start_brief(callback: CallbackQuery, state: FSMContext, db):
    user_id = callback.from_user.id if callback.from_user else 0
    latest = await db.get_latest_lead_by_user(user_id)
    if latest:
        created = datetime.fromisoformat(str(latest["created_at"]).replace(" ", "T"))
        if datetime.now() - created < timedelta(minutes=COOLDOWN_MINUTES):
            await callback.message.answer(
                f"Новая заявка доступна через {COOLDOWN_MINUTES} минут после предыдущей.",
                reply_markup=back_home_keyboard("main"),
            )
            await callback.answer()
            return

    await db.log_event(user_id, "brief_started", {})
    await state.clear()
    await state.set_state(BriefStates.project_type)
    await callback.message.answer("1) Какой тип проекта?", reply_markup=project_type_keyboard())
    await callback.answer()


@router.callback_query(BriefStates.project_type, F.data.startswith("brief:type:"))
async def brief_project_type(callback: CallbackQuery, state: FSMContext):
    await state.update_data(project_type=callback.data.split("brief:type:", 1)[1])
    await state.set_state(BriefStates.payment)
    await callback.message.answer("2) Нужна ли онлайн-оплата?", reply_markup=yes_no_keyboard("brief:payment"))
    await callback.answer()


@router.callback_query(BriefStates.payment, F.data.startswith("brief:payment:"))
async def brief_payment(callback: CallbackQuery, state: FSMContext):
    await state.update_data(payment=normalize_yes_no(callback.data.rsplit(":", 1)[1]))
    await state.set_state(BriefStates.design)
    await callback.message.answer("3) Есть ли готовый дизайн?", reply_markup=yes_no_keyboard("brief:design"))
    await callback.answer()


@router.callback_query(BriefStates.design, F.data.startswith("brief:design:"))
async def brief_design(callback: CallbackQuery, state: FSMContext):
    await state.update_data(design=normalize_yes_no(callback.data.rsplit(":", 1)[1]))
    await state.set_state(BriefStates.admin_panel)
    await callback.message.answer("4) Нужна ли админ-панель?", reply_markup=yes_no_keyboard("brief:admin"))
    await callback.answer()


@router.callback_query(BriefStates.admin_panel, F.data.startswith("brief:admin:"))
async def brief_admin_panel(callback: CallbackQuery, state: FSMContext):
    await state.update_data(admin_panel=normalize_yes_no(callback.data.rsplit(":", 1)[1]))
    await state.set_state(BriefStates.budget)
    await callback.message.answer("5) Какой у вас бюджет?", reply_markup=budget_keyboard())
    await callback.answer()


@router.callback_query(BriefStates.budget, F.data.startswith("brief:budget:"))
async def brief_budget(callback: CallbackQuery, state: FSMContext):
    mapping = {"low": "До 300$", "mid": "300–1000$", "high": "1000$+"}
    await state.update_data(budget=mapping[callback.data.rsplit(":", 1)[1]])
    await state.set_state(BriefStates.contact)
    await callback.message.answer("6) Ваш Telegram / номер телефона")
    await callback.answer()


@router.message(BriefStates.contact)
async def brief_contact(message: Message, state: FSMContext, db, bot, config, reminder_scheduler):
    data = await state.get_data()
    contact = (message.text or "").strip()
    user_id = message.from_user.id if message.from_user else 0
    tag = detect_tag(data.get("project_type", "-"), data.get("budget", "До 300$"))

    lead_id = await db.create_lead(
        user_id=user_id,
        project_type=data.get("project_type", "-"),
        payment=data.get("payment", "-"),
        design=data.get("design", "-"),
        admin_panel=data.get("admin_panel", "-"),
        budget=data.get("budget", "-"),
        contact=contact,
        tag=tag,
    )
    await db.log_event(user_id, "brief_submitted", {"lead_id": lead_id, "tag": tag})

    firestore_payload = {
        "client_name": (message.from_user.full_name if message.from_user else "") or "Без имени",
        "phone": contact,
        "site_type": data.get("project_type", "-"),
        "budget": data.get("budget", "-"),
        "payment": data.get("payment", "-"),
        "design": data.get("design", "-"),
        "admin_panel": data.get("admin_panel", "-"),
        "tag": tag,
        "user_id": user_id,
        "source": "telegram_bot",
        "sqlite_lead_id": lead_id,
        "is_processed": False,
        "created_at": datetime.utcnow().isoformat(),
    }
    await asyncio.to_thread(
        get_firestore_client(os.getenv("FIREBASE_CREDENTIALS")).collection("orders").add,
        firestore_payload,
    )

    lead = await db.get_lead(lead_id)
    if lead and lead["reminder_at"]:
        reminder_scheduler.schedule(lead_id, user_id, lead["reminder_at"])

    await notify_admin_new_lead(
        bot=bot,
        admin_id=config.admin_id,
        lead={
            "id": lead_id,
            "project_type": data.get("project_type", "-"),
            "payment": data.get("payment", "-"),
            "design": data.get("design", "-"),
            "admin_panel": data.get("admin_panel", "-"),
            "budget": data.get("budget", "-"),
            "tag": tag,
            "contact": contact,
        },
    )

    thanks = await db.get_setting("text_thanks_after_brief")
    await message.answer(thanks, reply_markup=post_brief_keyboard())
    await state.clear()
