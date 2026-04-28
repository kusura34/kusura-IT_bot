import json
from aiohttp import web
from aiogram import Router, F
from aiogram.types import CallbackQuery

router = Router()


@router.callback_query(F.data == "menu:demo")
async def show_demo(callback: CallbackQuery, db):
    enabled = await db.get_setting("demo_enabled", "1")
    if enabled != "1":
        from keyboards.navigation import back_home_keyboard
        await callback.message.answer("Раздел демо временно отключен.", reply_markup=back_home_keyboard("main"))
        await callback.answer()
        return

    demo_url = await db.get_setting("demo_url")
    text = await db.get_setting("text_demo_intro")

    await db.log_event(callback.from_user.id if callback.from_user else None, "demo_opened", {"url": demo_url})
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    kb = InlineKeyboardBuilder()
    kb.button(text="Открыть демо", url=demo_url)
    kb.button(text="⬅ Назад", callback_data="nav:back:main")
    kb.button(text="🏠 Главное меню", callback_data="nav:home")
    kb.adjust(1)

    await callback.message.answer(text, reply_markup=kb.as_markup())
    await callback.answer()


async def demo_webhook(request: web.Request) -> web.Response:
    db = request.app["db"]
    bot = request.app["bot"]

    data = await request.json()
    user_id = data.get("user_id")
    payload = json.dumps(data, ensure_ascii=False)

    await db.log_event(user_id, "demo_action_success", payload)

    if user_id:
        text = await db.get_setting("text_demo_success")
        await bot.send_message(chat_id=int(user_id), text=text)

    return web.json_response({"ok": True})
