# This file is part of owo-dusk.
#
# Copyright (c) 2024-present EchoQuill
#
# Portions of this file are based on code by EchoQuill, licensed under the
# GNU General Public License v3.0 (GPL-3.0).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import asyncio

from discord.ext import commands
from discord.ext.commands import ExtensionNotLoaded

from core.cogs._BASE import BaseCog


class Cookie(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.cmd = {
            "cmd_name": self.bot.alias["cookie"]["normal"],
            "cmd_arguments": "",
            "prefix": True,
            "checks": True,
            "id": "cookie",
        }

    @property
    def cooldowns(self):
        return self.bot.settings_dict.cooldowns

    @property
    def settings(self):
        return self.bot.settings_dict.commands.cookie

    async def start_cookie(self):
        last_cookie_time = await self.bot.db.fetch_cmd_lastran_time("cookie")

        if not self.bot.should_run(last_cookie_time):
            await asyncio.sleep(self.bot.calc_time())  # Wait until next 12:00 AM PST

        await self.bot.sleep_till(self.cooldowns.moderateCooldown)
        self.cmd["cmd_arguments"] = (
            f"<@{self.settings.user_id}>"
            if self.settings.ping_user
            else f"{self.settings.user_id}"
        )
        await self.bot.ch.put_queue(self.cmd, priority=True)

        self.bot.db.update_cmd_lastran_time("cookie")

    async def cog_load(self):
        if not self.settings.enabled:
            try:
                asyncio.create_task(self.bot.unload_cog("core.cogs.cookie"))
            except ExtensionNotLoaded:
                pass
        else:
            asyncio.create_task(self.start_cookie())

    async def cog_unload(self):
        await self.bot.ch.remove_queue(id="cookie")

    @commands.Cog.listener()
    async def on_message(self, message):
        nick = self.bot.get_nick(message)
        if (
            message.channel.id == self.bot.cm.id
            and message.author.id == self.bot.owo_bot_id
        ):
            if (
                "You got a cookie from" in message.content
                or "Nu! You need to wait" in message.content
            ):
                if nick in message.content or f"<@{self.bot.user.id}>":
                    """
                    'Nu! You need to wait' will get triggered unlike slow down one
                    as the actual command slowdown is different from this.
                    """
                    await self.bot.ch.remove_queue(id="cookie")

                    await asyncio.sleep(self.bot.calc_time())
                    await self.bot.sleep_till(self.cooldowns.moderateCooldown)
                    await self.bot.ch.put_queue(self.cmd, priority=True)

                    self.bot.db.update_cmd_lastran_time("cookie")


async def setup(bot):
    await bot.add_cog(Cookie(bot))
