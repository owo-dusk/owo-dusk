# This file is part of owo-dusk.
#
# Copyright (c) 2024-present EchoQuill

import asyncio

from discord.ext import commands
from discord.ext.commands import ExtensionNotLoaded
from cogs._BASE import BaseCog


class Run(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.cmd = {
            "cmd_name": self.bot.alias["run"]["normal"],
            "prefix": True,
            "checks": True,
            "id": "run",
        }
        self.completed_today = False
        self.tomorrow_task = None

    @property
    def settings(self):
        return self.bot.settings_dict_temp.commands.run

    async def cog_load(self):
        if not self.settings.enabled:
            try:
                asyncio.create_task(self.bot.unload_cog("cogs.run"))
            except ExtensionNotLoaded:
                pass
        else:
            asyncio.create_task(self.send_run(startup=True))

    async def cog_unload(self):
        await self.bot.remove_queue(id="run")
        if self.tomorrow_task and not self.tomorrow_task.done():
            self.tomorrow_task.cancel()

    def is_final_message(self, content: str):
        return "You are too tired to run!" in content

    def is_run_response(self, content: str):
        return self.is_final_message(content) or "You ran " in content

    async def mark_complete_today(self):
        self.completed_today = True
        self.bot.db.update_cmd_lastran_time("run")
        await self.bot.remove_queue(id="run")

        if self.tomorrow_task and not self.tomorrow_task.done():
            self.tomorrow_task.cancel()
        self.tomorrow_task = asyncio.create_task(self.resume_tomorrow())

    async def resume_tomorrow(self):
        await asyncio.sleep(self.bot.calc_time())
        self.completed_today = False
        await self.send_run(startup=True)

    async def send_run(self, startup=False):
        if self.completed_today:
            return

        if startup:
            last_ran = await self.bot.db.fetch_cmd_lastran_time("run")
            if not self.bot.should_run(last_ran):
                self.completed_today = True
                self.tomorrow_task = asyncio.create_task(self.resume_tomorrow())
                return
            await self.bot.sleep_till(self.bot.settings_dict_temp.cooldowns.shortCooldown)
        else:
            await self.bot.remove_queue(id="run")
            await self.bot.sleep(self.settings.get_cd())
            if self.completed_today:
                return

        await self.bot.put_queue(self.cmd)

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.channel.id == self.bot.cm.id:
            return

        if message.author.id != self.bot.owo_bot_id:
            return

        if self.is_final_message(message.content):
            await self.mark_complete_today()
            return

        if self.is_run_response(message.content):
            await self.send_run()


async def setup(bot):
    await bot.add_cog(Run(bot))
