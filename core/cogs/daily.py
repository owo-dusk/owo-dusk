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
import re

from discord.ext import commands
from discord.ext.commands import ExtensionNotLoaded

from core.cogs._BASE import BaseCog

cmd = {"cmd_name": "daily", "prefix": True, "checks": True, "id": "daily"}


class Daily(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)

    @property
    def cooldowns(self):
        return self.bot.settings_dict.cooldowns

    async def start_daily(self):
        last_daily_time = await self.bot.db.fetch_cmd_lastran_time("daily")

        if not self.bot.should_run(
            last_daily_time
        ):  # 86400 = seconds till a day(24hrs).
            await asyncio.sleep(self.bot.calc_time())  # Wait until next 12:00 AM PST

        await self.bot.sleep_till(self.cooldowns.briefCooldown)
        await self.bot.ch.put_queue(cmd, priority=True)
        await self.bot.ch.set_stat(False)

        self.bot.db.update_cmd_lastran_time("daily")

    async def cog_load(self):
        if not self.bot.settings_dict.daily:
            try:
                asyncio.create_task(self.bot.unload_cog("core.cogs.daily"))
            except ExtensionNotLoaded:
                pass
        else:
            asyncio.create_task(self.start_daily())

    async def cog_unload(self):
        await self.bot.ch.remove_queue(id="daily")

    @commands.Cog.listener()
    async def on_message(self, message):
        nick = self.bot.get_nick(message)

        if (
            message.channel.id == self.bot.cm.id
            and message.author.id == self.bot.owo_bot_id
            and nick in message.content
        ):
            if "Here is your daily **<:cowoncy:416043450337853441>" in message.content:
                """Task: add cash check regex here"""
                await self.bot.ch.remove_queue(cmd)
                await self.bot.ch.set_stat(True)
                await asyncio.sleep(self.bot.calc_time())

                self.bot.update_cash(
                    int(
                        re.search(
                            r"Here is your daily \*\*<:cowoncy:\d+> ([\d,]+)",
                            message.content,
                        )
                        .group(1)
                        .replace(",", "")
                    )
                )

                await self.bot.sleep_till(self.cooldowns.moderateCooldown)
                await self.bot.ch.put_queue(cmd, priority=True)
                await self.bot.ch.set_stat(False)

                self.bot.db.update_cmd_lastran_time("daily")

                if self.bot.global_settings_dict.webhook.enabled:
                    await self.bot.send_webhook("daily_claim")

            if (
                "**⏱ |** Nu! **" in message.content
                and "! You need to wait" in message.content
            ):
                await self.bot.ch.remove_queue(cmd)
                await self.bot.ch.set_stat(True)
                await asyncio.sleep(self.bot.calc_time())
                await self.bot.sleep_till(self.cooldowns.moderateCooldown)
                await self.bot.ch.put_queue(cmd, priority=True)
                await self.bot.ch.set_stat(False)

                self.bot.db.update_cmd_lastran_time("daily")


async def setup(bot):
    await bot.add_cog(Daily(bot))
