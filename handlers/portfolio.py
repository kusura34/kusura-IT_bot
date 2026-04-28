from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile

from keyboards.navigation import back_home_keyboard
from keyboards.portfolio import project_card_keyboard, solutions_keyboard

router = Router()


@router.callback_query(F.data == "menu:portfolio")
async def show_portfolio(callback: CallbackQuery, db):
    user_id = callback.from_user.id if callback.from_user else None
    await db.log_event(user_id, "portfolio_view", {})

    projects = await db.list_projects(include_hidden=False)
    if not projects:
        await callback.message.answer("Портфолио пока пустое.", reply_markup=back_home_keyboard("main"))
        await callback.answer()
        return

    for project in projects:
        text = (
            f"<b>{project['title']}</b>\n"
            f"{project['description']}\n\n"
            f"<b>Стек:</b> {project['stack']}"
        )
        image = project["image"]
        if image:
            try:
                await callback.message.answer_photo(
                    photo=FSInputFile(image),
                    caption=text,
                    reply_markup=project_card_keyboard(project["demo_url"], project["github_url"]),
                )
            except Exception:
                await callback.message.answer(text, reply_markup=project_card_keyboard(project["demo_url"], project["github_url"]))
        else:
            await callback.message.answer(text, reply_markup=project_card_keyboard(project["demo_url"], project["github_url"]))
    await callback.answer()


@router.callback_query(F.data == "menu:solutions")
async def show_ready_solutions(callback: CallbackQuery, db):
    rows = await db.list_ready_solutions(include_hidden=False)
    if not rows:
        await callback.message.answer("Раздел пока пуст.", reply_markup=back_home_keyboard("main"))
        await callback.answer()
        return

    for row in rows:
        text = (
            f"<b>{row['title']}</b>\n"
            f"{row['description']}\n\n"
            f"<b>Преимущества:</b> {row['benefits']}\n"
            f"<b>Пример использования:</b> {row['use_case']}"
        )
        await callback.message.answer(text, reply_markup=solutions_keyboard())
    await callback.answer()
