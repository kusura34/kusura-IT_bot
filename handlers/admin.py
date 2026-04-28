from __future__ import annotations

import asyncio
import csv
import os
import tempfile

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from firebase_admin import firestore

from keyboards.admin import (
    admin_menu_keyboard,
    contacts_edit_keyboard,
    faq_cms_keyboard,
    faq_select_keyboard,
    id_select_keyboard,
    leads_cms_keyboard,
    portfolio_cms_keyboard,
    project_edit_field_keyboard,
    project_edit_select_keyboard,
    settings_cms_keyboard,
    solutions_cms_keyboard,
    texts_edit_keyboard,
)
from services.firebase_client import get_firestore_client
from states.admin import (
    AddProjectStates,
    ContactEditStates,
    EditProjectStates,
    FaqStates,
    ProjectOrderStates,
    ReadySolutionStates,
    ReadySolutionEditStates,
    SettingEditStates,
    TextEditStates,
)

router = Router()


def is_admin(user_id: int, admin_id: int) -> bool:
    return user_id == admin_id


async def deny_if_not_admin(callback: CallbackQuery, config) -> bool:
    if not callback.from_user or not is_admin(callback.from_user.id, config.admin_id):
        await callback.answer("Нет доступа", show_alert=True)
        return True
    return False


@router.message(Command("admin"))
async def admin_menu(message: Message, config):
    if not message.from_user or not is_admin(message.from_user.id, config.admin_id):
        await message.answer("Доступ запрещен")
        return
    await message.answer("<b>Личная CMS</b>", reply_markup=admin_menu_keyboard())


@router.callback_query(F.data == "admin:back")
async def admin_back(callback: CallbackQuery, config):
    if await deny_if_not_admin(callback, config):
        return
    await callback.message.answer("<b>Личная CMS</b>", reply_markup=admin_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin:portfolio")
async def admin_portfolio_section(callback: CallbackQuery, config):
    if await deny_if_not_admin(callback, config):
        return
    await callback.message.answer("Раздел Портфолио", reply_markup=portfolio_cms_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin:faq")
async def admin_faq_section(callback: CallbackQuery, config):
    if await deny_if_not_admin(callback, config):
        return
    await callback.message.answer("Раздел FAQ", reply_markup=faq_cms_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin:leads")
async def admin_leads_section(callback: CallbackQuery, config):
    if await deny_if_not_admin(callback, config):
        return
    await callback.message.answer("Раздел Заявки", reply_markup=leads_cms_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin:solutions")
async def admin_solutions_section(callback: CallbackQuery, config):
    if await deny_if_not_admin(callback, config):
        return
    await callback.message.answer("Готовые решения", reply_markup=solutions_cms_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin:projects:add")
async def admin_project_add_start(callback: CallbackQuery, config, state: FSMContext):
    if await deny_if_not_admin(callback, config):
        return
    await state.clear()
    await state.set_state(AddProjectStates.title)
    await callback.message.answer("Название проекта:")
    await callback.answer()


@router.message(AddProjectStates.title)
async def add_project_title(message: Message, state: FSMContext):
    await state.update_data(title=(message.text or "").strip())
    await state.set_state(AddProjectStates.description)
    await message.answer("Описание:")


@router.message(AddProjectStates.description)
async def add_project_description(message: Message, state: FSMContext):
    await state.update_data(description=(message.text or "").strip())
    await state.set_state(AddProjectStates.stack)
    await message.answer("Стек:")


@router.message(AddProjectStates.stack)
async def add_project_stack(message: Message, state: FSMContext):
    await state.update_data(stack=(message.text or "").strip())
    await state.set_state(AddProjectStates.image)
    await message.answer("Путь к фото (или -):")


@router.message(AddProjectStates.image)
async def add_project_image(message: Message, state: FSMContext):
    image = (message.text or "").strip()
    await state.update_data(image="" if image == "-" else image)
    await state.set_state(AddProjectStates.demo_url)
    await message.answer("Demo link:")


@router.message(AddProjectStates.demo_url)
async def add_project_demo(message: Message, state: FSMContext):
    await state.update_data(demo_url=(message.text or "").strip())
    await state.set_state(AddProjectStates.github_url)
    await message.answer("GitHub link (или -):")


@router.message(AddProjectStates.github_url)
async def add_project_github(message: Message, state: FSMContext, db):
    github = (message.text or "").strip()
    data = await state.get_data()
    max_sort = await db.get_max_project_sort_order()
    await db.create_project(
        title=data.get("title", ""),
        description=data.get("description", ""),
        stack=data.get("stack", ""),
        image=data.get("image", ""),
        demo_url=data.get("demo_url", ""),
        github_url="" if github == "-" else github,
        is_visible=1,
        sort_order=max_sort + 1,
    )
    await state.clear()
    await message.answer("Проект добавлен", reply_markup=admin_menu_keyboard())


@router.callback_query(F.data == "admin:projects:delete")
async def admin_projects_delete_menu(callback: CallbackQuery, config, db):
    if await deny_if_not_admin(callback, config):
        return
    ids = await db.list_project_ids_desc()
    await callback.message.answer("Выберите ID проекта:", reply_markup=id_select_keyboard("admin:project:delete", ids))
    await callback.answer()


@router.callback_query(F.data.startswith("admin:project:delete:"))
async def admin_project_delete(callback: CallbackQuery, config, db):
    if await deny_if_not_admin(callback, config):
        return
    await db.delete_project(int(callback.data.rsplit(":", 1)[1]))
    await callback.answer("Удалено")


@router.callback_query(F.data == "admin:projects:toggle")
async def admin_projects_toggle_menu(callback: CallbackQuery, config, db):
    if await deny_if_not_admin(callback, config):
        return
    rows = await db.list_projects(include_hidden=True)
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    kb = InlineKeyboardBuilder()
    for r in rows:
        status = "✅" if r["is_visible"] else "❌"
        kb.button(text=f"{status} #{r['id']} {r['title']}", callback_data=f"admin:project:toggle:{r['id']}")
    kb.button(text="⬅ Назад", callback_data="admin:back")
    kb.adjust(1)
    await callback.message.answer("Скрыть/Показать проекты", reply_markup=kb.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("admin:project:toggle:"))
async def admin_project_toggle_one(callback: CallbackQuery, config, db):
    if await deny_if_not_admin(callback, config):
        return
    pid = int(callback.data.rsplit(":", 1)[1])
    row = await db.get_project(pid)
    if row:
        await db.update_project_fields(pid, {"is_visible": 0 if row["is_visible"] else 1})
    await callback.answer("Обновлено")


@router.callback_query(F.data == "admin:projects:order")
async def admin_projects_order_menu(callback: CallbackQuery, config, db, state: FSMContext):
    if await deny_if_not_admin(callback, config):
        return
    rows = await db.list_projects(include_hidden=True)
    if not rows:
        await callback.message.answer("Нет проектов")
        await callback.answer()
        return

    await state.clear()
    kb = InlineKeyboardBuilder()
    for r in rows:
        kb.button(text=f"#{r['id']} {r['title']} → {r['sort_order']}", callback_data=f"admin:project:orderpick:{r['id']}")
    kb.button(text="⬅ Назад", callback_data="admin:back")
    kb.adjust(1)
    await callback.message.answer("Выберите проект, чтобы изменить порядок отображения:", reply_markup=kb.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("admin:project:orderpick:"))
async def admin_project_order_pick(callback: CallbackQuery, config, state: FSMContext):
    if await deny_if_not_admin(callback, config):
        return
    project_id = int(callback.data.rsplit(":", 1)[1])
    await state.clear()
    await state.update_data(project_id=project_id)
    await state.set_state(ProjectOrderStates.value)
    await callback.message.answer("Отправьте новое число для `sort_order` (например 1, 2, 3 ...):")
    await callback.answer()


@router.message(ProjectOrderStates.value, F.text)
async def admin_project_order_save(message: Message, state: FSMContext, db):
    data = await state.get_data()
    project_id = data.get("project_id")
    if not project_id:
        await state.clear()
        await message.answer("Сессия сброшена. Откройте изменение порядка заново.")
        return
    try:
        new_order = int((message.text or "").strip())
    except ValueError:
        await message.answer("Нужно отправить целое число (например 1).")
        return
    await db.update_project_fields(int(project_id), {"sort_order": new_order})
    await state.clear()
    await message.answer("Порядок обновлен ✅", reply_markup=admin_menu_keyboard())


@router.callback_query(F.data == "admin:projects:edit")
async def admin_projects_edit_help(callback: CallbackQuery, config, db):
    if await deny_if_not_admin(callback, config):
        return
    rows = await db.list_projects(include_hidden=True)
    if not rows:
        await callback.message.answer("Проектов пока нет")
        await callback.answer()
        return
    items = [(row["id"], row["title"]) for row in rows]
    await callback.message.answer("Выберите проект для редактирования:", reply_markup=project_edit_select_keyboard(items))
    await callback.answer()


@router.callback_query(F.data.startswith("admin:project:editpick:"))
async def admin_project_edit_pick(callback: CallbackQuery, config, state: FSMContext):
    if await deny_if_not_admin(callback, config):
        return
    project_id = int(callback.data.rsplit(":", 1)[1])
    await state.clear()
    await state.update_data(project_id=project_id)
    await state.set_state(EditProjectStates.field)
    await callback.message.answer("Какое поле изменить?", reply_markup=project_edit_field_keyboard())
    await callback.answer()


@router.callback_query(EditProjectStates.field, F.data.startswith("admin:project:field:"))
async def admin_project_edit_field(callback: CallbackQuery, state: FSMContext):
    field = callback.data.rsplit(":", 1)[1]
    allowed = {"title", "description", "stack", "image", "demo_url", "github_url"}
    if field not in allowed:
        await callback.answer("Неизвестное поле", show_alert=True)
        return
    await state.update_data(field=field)
    await state.set_state(EditProjectStates.value)
    await callback.message.answer("Отправьте новое значение:")
    await callback.answer()


@router.message(EditProjectStates.value)
async def admin_project_edit_value(message: Message, state: FSMContext, db):
    data = await state.get_data()
    project_id = data.get("project_id")
    field = data.get("field")
    allowed = {"title", "description", "stack", "image", "demo_url", "github_url"}
    if not project_id or field not in allowed:
        await state.clear()
        await message.answer("Сессия редактирования сброшена. Откройте редактирование проекта заново.")
        return

    value = (message.text or "").strip()
    await db.update_project_fields(int(project_id), {field: value})
    await state.clear()
    await message.answer("Проект обновлен ✅", reply_markup=admin_menu_keyboard())


@router.callback_query(F.data == "admin:faq:add")
async def admin_faq_add_start(callback: CallbackQuery, config, state: FSMContext):
    if await deny_if_not_admin(callback, config):
        return
    await state.clear()
    await state.update_data(faq_mode="add")
    await state.set_state(FaqStates.question)
    await callback.message.answer("Введите вопрос FAQ:")
    await callback.answer()


@router.message(FaqStates.question, F.text)
async def faq_question(message: Message, state: FSMContext):
    await state.update_data(question=(message.text or "").strip())
    await state.set_state(FaqStates.answer)
    data = await state.get_data()
    await message.answer("Введите новый ответ:" if data.get("faq_mode") == "edit" else "Введите ответ:")


@router.message(FaqStates.answer, F.text)
async def faq_answer(message: Message, state: FSMContext, db):
    data = await state.get_data()
    if data.get("faq_mode") == "edit" and data.get("faq_id"):
        await db.update_faq(int(data["faq_id"]), data.get("question", ""), (message.text or "").strip())
        done_text = "FAQ обновлен ✅"
    else:
        await db.add_faq(question=data.get("question", ""), answer=(message.text or "").strip())
        done_text = "FAQ добавлен ✅"
    await state.clear()
    await message.answer(done_text, reply_markup=admin_menu_keyboard())


@router.callback_query(F.data == "admin:faq:delete")
async def admin_faq_delete_menu(callback: CallbackQuery, config, db):
    if await deny_if_not_admin(callback, config):
        return
    rows = await db.list_faq_items()
    await callback.message.answer("Выберите FAQ ID:", reply_markup=id_select_keyboard("admin:faq:delete:id", [r["id"] for r in rows]))
    await callback.answer()


@router.callback_query(F.data.startswith("admin:faq:delete:id:"))
async def admin_faq_delete(callback: CallbackQuery, config, db):
    if await deny_if_not_admin(callback, config):
        return
    await db.delete_faq(int(callback.data.rsplit(":", 1)[1]))
    await callback.answer("Удалено")


@router.callback_query(F.data == "admin:faq:edit")
async def admin_faq_edit_help(callback: CallbackQuery, config, db):
    if await deny_if_not_admin(callback, config):
        return
    rows = await db.list_faq_items()
    items = [(row["id"], row["question"]) for row in rows]
    if not items:
        await callback.message.answer("FAQ пока пуст")
        await callback.answer()
        return
    await callback.message.answer("Выберите вопрос для редактирования:", reply_markup=faq_select_keyboard(items, "admin:faq:editpick"))
    await callback.answer()


@router.callback_query(F.data.startswith("admin:faq:editpick:"))
async def admin_faq_edit_pick(callback: CallbackQuery, config, state: FSMContext):
    if await deny_if_not_admin(callback, config):
        return
    faq_id = int(callback.data.rsplit(":", 1)[1])
    await state.clear()
    await state.update_data(faq_mode="edit", faq_id=faq_id)
    await state.set_state(FaqStates.question)
    await callback.message.answer("Введите новый вопрос:")
    await callback.answer()


@router.callback_query(F.data.startswith("admin:faq:update:"))
async def admin_faq_update(callback: CallbackQuery, config, db):
    if await deny_if_not_admin(callback, config):
        return
    _, _, _, sid, payload = callback.data.split(":", 4)
    if "|" in payload:
        q, a = payload.split("|", 1)
        await db.update_faq(int(sid), q, a)
    await callback.answer("FAQ обновлен")


@router.callback_query(F.data == "admin:contacts")
async def admin_contacts(callback: CallbackQuery, config):
    if await deny_if_not_admin(callback, config):
        return
    await callback.message.answer("Выберите, какой контакт изменить:", reply_markup=contacts_edit_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("admin:contact:pick:"))
async def admin_contact_pick(callback: CallbackQuery, config, state: FSMContext):
    if await deny_if_not_admin(callback, config):
        return
    key = callback.data.rsplit(":", 1)[1]
    await state.clear()
    await state.update_data(contact_key=key)
    await state.set_state(ContactEditStates.value)
    await callback.message.answer("Отправьте новое значение:")
    await callback.answer()


@router.callback_query(F.data.startswith("admin:contact:set:"))
async def admin_contact_set(callback: CallbackQuery, config, db):
    if await deny_if_not_admin(callback, config):
        return
    _, _, _, key, value = callback.data.split(":", 4)
    if key in {"telegram", "whatsapp", "email"}:
        await db.set_setting(f"contact_{key}", value)
    await callback.answer("Контакт обновлен")


@router.callback_query(F.data == "admin:texts")
async def admin_texts(callback: CallbackQuery, config):
    if await deny_if_not_admin(callback, config):
        return
    await callback.message.answer("Выберите текст для редактирования:", reply_markup=texts_edit_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("admin:text:pick:"))
async def admin_text_pick(callback: CallbackQuery, config, state: FSMContext):
    if await deny_if_not_admin(callback, config):
        return
    key = callback.data.rsplit(":", 1)[1]
    await state.clear()
    await state.update_data(text_key=key)
    await state.set_state(TextEditStates.value)
    await callback.message.answer("Отправьте новый текст:")
    await callback.answer()


@router.callback_query(F.data.startswith("admin:text:set:"))
async def admin_text_set(callback: CallbackQuery, config, db):
    if await deny_if_not_admin(callback, config):
        return
    _, _, _, key, value = callback.data.split(":", 4)
    await db.set_setting(f"text_{key}", value)
    await callback.answer("Текст обновлен")


@router.message(ContactEditStates.value, F.text)
async def admin_contact_save(message: Message, state: FSMContext, db):
    data = await state.get_data()
    key = data.get("contact_key")
    if key not in {"telegram", "whatsapp", "email"}:
        await state.clear()
        await message.answer("Сессия редактирования сброшена.")
        return
    await db.set_setting(f"contact_{key}", (message.text or "").strip())
    await state.clear()
    await message.answer("Контакт обновлен ✅", reply_markup=admin_menu_keyboard())


@router.message(TextEditStates.value, F.text)
async def admin_text_save(message: Message, state: FSMContext, db):
    data = await state.get_data()
    key = data.get("text_key")
    allowed = {"welcome", "thanks_after_brief", "demo_intro", "demo_success", "reminder"}
    if key not in allowed:
        await state.clear()
        await message.answer("Сессия редактирования сброшена.")
        return
    await db.set_setting(f"text_{key}", (message.text or "").strip())
    await state.clear()
    await message.answer("Текст обновлен ✅", reply_markup=admin_menu_keyboard())


@router.callback_query(F.data == "admin:settings")
async def admin_settings(callback: CallbackQuery, config, db):
    if await deny_if_not_admin(callback, config):
        return
    demo_url = await db.get_setting("demo_url")
    await callback.message.answer(
        f"Текущая demo-ссылка:\n{demo_url}",
        reply_markup=settings_cms_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:setting:edit_demo_url")
async def admin_setting_demo_url_start(callback: CallbackQuery, config, state: FSMContext):
    if await deny_if_not_admin(callback, config):
        return
    await state.clear()
    await state.set_state(SettingEditStates.value)
    await state.update_data(setting_key="demo_url")
    await callback.message.answer("Отправьте новую ссылку для раздела «Живая демонстрация».")
    await callback.answer()


@router.callback_query(F.data.startswith("admin:setting:set:demo_url:"))
async def admin_set_demo_url(callback: CallbackQuery, config, db):
    if await deny_if_not_admin(callback, config):
        return
    await db.set_setting("demo_url", callback.data.split("admin:setting:set:demo_url:", 1)[1])
    await callback.answer("Demo URL обновлен")


@router.message(SettingEditStates.value)
async def admin_setting_demo_url_save(message: Message, state: FSMContext, db):
    data = await state.get_data()
    if data.get("setting_key") != "demo_url":
        return
    new_url = (message.text or "").strip()
    if not (new_url.startswith("http://") or new_url.startswith("https://")):
        await message.answer("Ссылка должна начинаться с http:// или https://")
        return
    await db.set_setting("demo_url", new_url)
    await state.clear()
    await message.answer("Ссылка демо обновлена ✅", reply_markup=admin_menu_keyboard())


@router.callback_query(F.data.startswith("admin:setting:demo:"))
async def admin_toggle_demo(callback: CallbackQuery, config, db):
    if await deny_if_not_admin(callback, config):
        return
    await db.set_setting("demo_enabled", "1" if callback.data.rsplit(":", 1)[1] == "on" else "0")
    await callback.answer("Обновлено")


@router.callback_query(F.data == "admin:leads:list")
async def admin_leads_list(callback: CallbackQuery, config, db):
    if await deny_if_not_admin(callback, config):
        return
    leads = await db.list_leads(limit=100)
    for lead in leads:
        status = "обработано" if lead["is_processed"] else "новая"
        await callback.message.answer(f"<b>#{lead['id']}</b> [{status}] ({lead['tag']})\n{lead['project_type']} | {lead['budget']} | {lead['contact']}")
    await callback.answer()


@router.callback_query(F.data == "admin:leads:firestore")
async def admin_firestore_leads_list(callback: CallbackQuery, config):
    if await deny_if_not_admin(callback, config):
        return

    docs = await asyncio.to_thread(
        lambda: list(
            get_firestore_client(os.getenv("FIREBASE_CREDENTIALS"))
            .collection("orders")
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(30)
            .stream()
        )
    )
    if not docs:
        await callback.message.answer("В Firestore пока нет заказов")
        await callback.answer()
        return

    for doc in docs:
        data = doc.to_dict() or {}
        client_name = data.get("client_name") or data.get("name") or "Не указано"
        phone = data.get("phone") or data.get("contact") or "Не указано"
        site_type = data.get("site_type") or data.get("project_type") or "Не указано"
        status = "обработано" if data.get("is_processed") else "новая"

        kb = InlineKeyboardBuilder()
        kb.button(text="✅ Обработано", callback_data=f"fire:order:process:{doc.id}")
        kb.button(text="🗑 Удалить", callback_data=f"fire:order:delete:{doc.id}")
        kb.adjust(2)

        await callback.message.answer(
            f"<b>Firestore #{doc.id}</b> [{status}]\n"
            f"Клиент: {client_name}\n"
            f"Телефон: {phone}\n"
            f"Тип сайта: {site_type}",
            reply_markup=kb.as_markup(),
        )

    await callback.answer()


@router.callback_query(F.data == "admin:leads:view")
async def admin_lead_view_hint(callback: CallbackQuery, config, db):
    if await deny_if_not_admin(callback, config):
        return
    ids = await db.list_lead_ids(limit=60)
    if not ids:
        await callback.message.answer("Заявок пока нет")
        await callback.answer()
        return
    await callback.message.answer("Выберите заявку:", reply_markup=id_select_keyboard("admin:lead:view", ids))
    await callback.answer()


@router.callback_query(F.data.startswith("admin:lead:view:"))
async def admin_lead_view(callback: CallbackQuery, config, db):
    if await deny_if_not_admin(callback, config):
        return
    lead = await db.get_lead(int(callback.data.rsplit(":", 1)[1]))
    if lead:
        await callback.message.answer(
            f"<b>Заявка #{lead['id']}</b>\nТип: {lead['project_type']}\nОплата: {lead['payment']}\n"
            f"Дизайн: {lead['design']}\nАдминка: {lead['admin_panel']}\nБюджет: {lead['budget']}\n"
            f"Тег: {lead['tag']}\nКонтакт: {lead['contact']}"
        )
    await callback.answer()


@router.callback_query(F.data == "admin:leads:process")
async def admin_lead_process_hint(callback: CallbackQuery, config, db):
    if await deny_if_not_admin(callback, config):
        return
    ids = await db.list_lead_ids(limit=60, only_unprocessed=True)
    if not ids:
        await callback.message.answer("Нет необработанных заявок")
        await callback.answer()
        return
    await callback.message.answer("Выберите заявку, чтобы пометить обработанной:", reply_markup=id_select_keyboard("admin:lead:process", ids))
    await callback.answer()


@router.callback_query(F.data.startswith("admin:lead:process:"))
async def admin_lead_process(callback: CallbackQuery, config, db, reminder_scheduler):
    if await deny_if_not_admin(callback, config):
        return
    lead_id = int(callback.data.rsplit(":", 1)[1])
    await db.mark_lead_processed(lead_id)
    reminder_scheduler.cancel(lead_id)
    await callback.answer("Готово")


@router.callback_query(F.data == "admin:leads:delete")
async def admin_lead_delete_hint(callback: CallbackQuery, config, db):
    if await deny_if_not_admin(callback, config):
        return
    ids = await db.list_lead_ids(limit=60)
    if not ids:
        await callback.message.answer("Заявок пока нет")
        await callback.answer()
        return
    await callback.message.answer("Выберите заявку для удаления:", reply_markup=id_select_keyboard("admin:lead:delete", ids))
    await callback.answer()


@router.callback_query(F.data.startswith("admin:lead:delete:"))
async def admin_lead_delete(callback: CallbackQuery, config, db, reminder_scheduler):
    if await deny_if_not_admin(callback, config):
        return
    lead_id = int(callback.data.rsplit(":", 1)[1])
    reminder_scheduler.cancel(lead_id)
    await db.delete_lead(lead_id)
    await callback.answer("Удалено")


@router.callback_query(F.data.startswith("fire:order:process:"))
async def process_firestore_order(callback: CallbackQuery, config):
    if await deny_if_not_admin(callback, config):
        return
    doc_id = callback.data.rsplit(":", 1)[1]
    await asyncio.to_thread(
        get_firestore_client(os.getenv("FIREBASE_CREDENTIALS")).collection("orders").document(doc_id).set,
        {"is_processed": True},
        merge=True,
    )
    await callback.answer("Заказ помечен обработанным")


@router.callback_query(F.data.startswith("fire:order:delete:"))
async def delete_firestore_order(callback: CallbackQuery, config):
    if await deny_if_not_admin(callback, config):
        return
    doc_id = callback.data.rsplit(":", 1)[1]
    await asyncio.to_thread(get_firestore_client(os.getenv("FIREBASE_CREDENTIALS")).collection("orders").document(doc_id).delete)
    await callback.answer("Заказ удален")


@router.callback_query(F.data == "admin:leads:csv")
async def admin_leads_csv(callback: CallbackQuery, config, db):
    if await deny_if_not_admin(callback, config):
        return
    rows = await db.list_leads(limit=None)
    with tempfile.NamedTemporaryFile("w+", newline="", encoding="utf-8", suffix=".csv") as fp:
        writer = csv.writer(fp)
        writer.writerow(["id", "user_id", "project_type", "payment", "design", "admin_panel", "budget", "contact", "tag", "is_processed", "created_at"])
        for r in rows:
            writer.writerow([r["id"], r["user_id"], r["project_type"], r["payment"], r["design"], r["admin_panel"], r["budget"], r["contact"], r["tag"], r["is_processed"], r["created_at"]])
        fp.seek(0)
        data = fp.read().encode("utf-8")
    await callback.message.answer_document(BufferedInputFile(data, filename="leads_export.csv"))
    await callback.answer()


@router.callback_query(F.data == "admin:stats")
async def admin_stats(callback: CallbackQuery, config, db):
    if await deny_if_not_admin(callback, config):
        return

    def pct(num: int, den: int) -> str:
        return f"{(num / den * 100):.1f}%" if den else "0%"

    users = await db.count_users()
    p = await db.count_demo_logs("portfolio_view")
    bs = await db.count_demo_logs("brief_started")
    bsub = await db.count_demo_logs("brief_submitted")
    d = await db.count_demo_logs("demo_opened")
    c = await db.count_demo_logs("contact_opened")

    await callback.message.answer(
        "<b>Статистика</b>\n"
        f"Портфолио: {p}\nЗапуск брифа: {bs}\nЗаполнен бриф: {bsub}\nОткрыли демо: {d}\nДошли до контактов: {c}\n\n"
        "<b>Конверсия</b>\n"
        f"Users -> Portfolio: {pct(p, users)}\n"
        f"Portfolio -> Brief submit: {pct(bsub, p)}\n"
        f"Brief started -> submit: {pct(bsub, bs)}\n"
        f"Users -> Contacts: {pct(c, users)}"
    )
    await callback.answer()


@router.callback_query(F.data == "admin:solutions:add")
async def admin_solution_add_start(callback: CallbackQuery, config, state: FSMContext):
    if await deny_if_not_admin(callback, config):
        return
    await state.clear()
    await state.set_state(ReadySolutionStates.title)
    await callback.message.answer("Название решения:")
    await callback.answer()


@router.message(ReadySolutionStates.title)
async def rs_title(message: Message, state: FSMContext):
    await state.update_data(title=(message.text or "").strip())
    await state.set_state(ReadySolutionStates.description)
    await message.answer("Описание:")


@router.message(ReadySolutionStates.description)
async def rs_desc(message: Message, state: FSMContext):
    await state.update_data(description=(message.text or "").strip())
    await state.set_state(ReadySolutionStates.benefits)
    await message.answer("Преимущества:")


@router.message(ReadySolutionStates.benefits)
async def rs_benefits(message: Message, state: FSMContext):
    await state.update_data(benefits=(message.text or "").strip())
    await state.set_state(ReadySolutionStates.use_case)
    await message.answer("Пример использования:")


@router.message(ReadySolutionStates.use_case)
async def rs_use_case(message: Message, state: FSMContext, db):
    data = await state.get_data()
    max_sort = await db.get_max_ready_solution_sort_order()
    await db.create_ready_solution(
        title=data.get("title", ""),
        description=data.get("description", ""),
        benefits=data.get("benefits", ""),
        use_case=(message.text or "").strip(),
        sort_order=max_sort + 1,
    )
    await state.clear()
    await message.answer("Решение добавлено", reply_markup=admin_menu_keyboard())


@router.callback_query(F.data == "admin:solutions:delete")
async def admin_solution_delete_hint(callback: CallbackQuery, config, db):
    if await deny_if_not_admin(callback, config):
        return
    ids = await db.list_ready_solution_ids()
    if not ids:
        await callback.message.answer("Готовых решений пока нет")
        await callback.answer()
        return
    await callback.message.answer("Выберите решение для удаления:", reply_markup=id_select_keyboard("admin:solution:delete", ids))
    await callback.answer()


@router.callback_query(F.data.startswith("admin:solution:delete:"))
async def admin_solution_delete(callback: CallbackQuery, config, db):
    if await deny_if_not_admin(callback, config):
        return
    await db.delete_ready_solution(int(callback.data.rsplit(":", 1)[1]))
    await callback.answer("Удалено")


@router.callback_query(F.data == "admin:solutions:edit")
async def admin_solution_edit_hint(callback: CallbackQuery, config, db):
    if await deny_if_not_admin(callback, config):
        return
    rows = await db.list_ready_solutions(include_hidden=True)
    if not rows:
        await callback.message.answer("Готовых решений пока нет")
        await callback.answer()
        return
    kb = InlineKeyboardBuilder()
    for r in rows:
        title = (r["title"] or "").strip() or "Без названия"
        kb.button(text=f"#{r['id']} {title[:40]}", callback_data=f"admin:solution:editpick:{r['id']}")
    kb.button(text="⬅ Назад", callback_data="admin:back")
    kb.adjust(1)
    await callback.message.answer("Выберите решение для редактирования:", reply_markup=kb.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("admin:solution:editpick:"))
async def admin_solution_edit_pick(callback: CallbackQuery, config, state: FSMContext):
    if await deny_if_not_admin(callback, config):
        return
    solution_id = int(callback.data.rsplit(":", 1)[1])
    await state.clear()
    await state.update_data(solution_id=solution_id)
    await state.set_state(ReadySolutionEditStates.field)

    kb = InlineKeyboardBuilder()
    kb.button(text="Название", callback_data="admin:solution:field:title")
    kb.button(text="Описание", callback_data="admin:solution:field:description")
    kb.button(text="Преимущества", callback_data="admin:solution:field:benefits")
    kb.button(text="Пример использования", callback_data="admin:solution:field:use_case")
    kb.button(text="Порядок (sort_order)", callback_data="admin:solution:field:sort_order")
    kb.button(text="Видимость (is_visible)", callback_data="admin:solution:field:is_visible")
    kb.button(text="⬅ Назад", callback_data="admin:back")
    kb.adjust(1)
    await callback.message.answer("Какое поле изменить?", reply_markup=kb.as_markup())
    await callback.answer()


@router.callback_query(ReadySolutionEditStates.field, F.data.startswith("admin:solution:field:"))
async def admin_solution_edit_field(callback: CallbackQuery, config, state: FSMContext):
    if await deny_if_not_admin(callback, config):
        return
    field = callback.data.rsplit(":", 1)[1]
    allowed = {"title", "description", "benefits", "use_case", "sort_order", "is_visible"}
    if field not in allowed:
        await callback.answer("Неизвестное поле", show_alert=True)
        return
    await state.update_data(field=field)
    if field == "is_visible":
        kb = InlineKeyboardBuilder()
        kb.button(text="Вкл", callback_data="admin:solution:visible:on")
        kb.button(text="Выкл", callback_data="admin:solution:visible:off")
        kb.button(text="⬅ Назад", callback_data="admin:back")
        kb.adjust(2, 1)
        await callback.message.answer("Видимость:", reply_markup=kb.as_markup())
        await callback.answer()
        return

    await state.set_state(ReadySolutionEditStates.value)
    await callback.message.answer("Отправьте новое значение:")
    await callback.answer()


@router.callback_query(ReadySolutionEditStates.field, F.data.startswith("admin:solution:visible:"))
async def admin_solution_edit_visible(callback: CallbackQuery, config, state: FSMContext, db):
    if await deny_if_not_admin(callback, config):
        return
    data = await state.get_data()
    solution_id = data.get("solution_id")
    if not solution_id:
        await state.clear()
        await callback.answer("Сессия сброшена", show_alert=True)
        return
    value = 1 if callback.data.rsplit(":", 1)[1] == "on" else 0
    await db.update_ready_solution_fields(int(solution_id), {"is_visible": value})
    await state.clear()
    await callback.message.answer("Решение обновлено ✅", reply_markup=admin_menu_keyboard())
    await callback.answer("Обновлено")


@router.message(ReadySolutionEditStates.value)
async def admin_solution_edit_value(message: Message, state: FSMContext, db):
    data = await state.get_data()
    solution_id = data.get("solution_id")
    field = data.get("field")
    allowed = {"title", "description", "benefits", "use_case", "sort_order"}
    if not solution_id or field not in allowed:
        await state.clear()
        await message.answer("Сессия редактирования сброшена. Откройте редактирование решения заново.")
        return

    value_raw = (message.text or "").strip()
    if field == "sort_order":
        try:
            value = int(value_raw)
        except ValueError:
            await message.answer("Для `sort_order` нужно целое число (например 1).")
            return
    else:
        value = value_raw

    await db.update_ready_solution_fields(int(solution_id), {field: value})
    await state.clear()
    await message.answer("Решение обновлено ✅", reply_markup=admin_menu_keyboard())


@router.callback_query(F.data.startswith("admin:solution:edit:"))
async def admin_solution_edit(callback: CallbackQuery, config, db):
    """
    Legacy handler (старый формат callback c value).
    Оставлен для совместимости, но больше не используется в UI.
    """
    if await deny_if_not_admin(callback, config):
        return
    try:
        _, _, _, sid, field, value = callback.data.split(":", 5)
    except ValueError:
        await callback.answer("Некорректные данные", show_alert=True)
        return
    if field in {"title", "description", "benefits", "use_case", "sort_order", "is_visible"}:
        if field in {"sort_order", "is_visible"}:
            try:
                value_to_set = int(str(value).strip())
            except ValueError:
                await callback.answer("Некорректное значение", show_alert=True)
                return
        else:
            value_to_set = value
        await db.update_ready_solution_fields(int(sid), {field: value_to_set})
    await callback.answer("Обновлено")
