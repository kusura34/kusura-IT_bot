from __future__ import annotations

from datetime import datetime, timezone

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger


class ReminderScheduler:
    def __init__(self, scheduler: AsyncIOScheduler, bot: Bot, db):
        self.scheduler = scheduler
        self.bot = bot
        self.db = db

    def _job_id(self, lead_id: int) -> str:
        return f"lead_reminder:{lead_id}"

    async def restore_jobs(self) -> None:
        leads = await self.db.list_pending_reminder_leads()
        now = datetime.now(timezone.utc)
        for lead in leads:
            if not lead["reminder_at"]:
                continue
            dt = datetime.fromisoformat(lead["reminder_at"])
            if dt <= now:
                await self.send_reminder(lead["id"], lead["user_id"])
            else:
                self.scheduler.add_job(
                    self.send_reminder,
                    trigger=DateTrigger(run_date=dt),
                    id=self._job_id(lead["id"]),
                    replace_existing=True,
                    args=[lead["id"], lead["user_id"]],
                )

    def schedule(self, lead_id: int, user_id: int, reminder_at: str) -> None:
        dt = datetime.fromisoformat(reminder_at)
        self.scheduler.add_job(
            self.send_reminder,
            trigger=DateTrigger(run_date=dt),
            id=self._job_id(lead_id),
            replace_existing=True,
            args=[lead_id, user_id],
        )

    def cancel(self, lead_id: int) -> None:
        jid = self._job_id(lead_id)
        if self.scheduler.get_job(jid):
            self.scheduler.remove_job(jid)

    async def send_reminder(self, lead_id: int, user_id: int) -> None:
        lead = await self.db.get_lead(lead_id)
        if not lead or lead["is_processed"] or lead["reminder_sent"]:
            return

        text = await self.db.get_setting("text_reminder", "Напоминаю по вашей заявке 👋\nЕсли у вас появились вопросы — можете написать мне.")
        await self.bot.send_message(user_id, text)
        await self.db.mark_lead_reminder_sent(lead_id)
