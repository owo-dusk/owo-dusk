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


class Lottery(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)

        self._cmd = {
            "cmd_name": self.bot.alias["lottery"]["normal"],
            "cmd_arguments": 0,
            "prefix": True,
            "checks": True,
            "id": "lottery",
        }

    @property
    def cooldown(self):
        return self.bot.settings_dict.cooldowns

    @property
    def settings(self):
        return self.bot.settings_dict.commands.lottery

    @property
    def cmd(self):
        self._cmd["cmd_arguments"] = self.settings.amount
        return self._cmd

    async def start_lottery(self):
        last_lottery_time = await self.bot.db.fetch_cmd_lastran_time("lottery")

        if not self.bot.should_run(last_lottery_time):
            await asyncio.sleep(self.bot.calc_time())  # Wait until next 12:00 AM PST

        await self.bot.sleep_till(self.cooldown.shortCooldown)
        await self.bot.ch.put_queue(self.cmd)

        self.bot.db.update_cmd_lastran_time("lottery")

    async def cog_load(self):
        if not self.settings.enabled:
            try:
                asyncio.create_task(self.bot.unload_cog("core.cogs.lottery"))
            except ExtensionNotLoaded:
                pass
        else:
            asyncio.create_task(self.start_lottery())

    async def cog_unload(self):
        await self.bot.ch.remove_queue(id="lottery")

    @commands.Cog.listener()
    async def on_message(self, message):
        nick = self.bot.get_nick(message)
        if (
            message.channel.id == self.bot.cm.id
            and message.author.id == self.bot.owo_bot_id
        ):
            if message.embeds:
                for embed in message.embeds:
                    if (
                        embed.author.name is not None
                        and f"{nick}'s Lottery Submission" in embed.author.name
                    ):
                        await self.bot.ch.remove_queue(id="lottery")
                        await asyncio.sleep(self.bot.calc_time())
                        await self.bot.sleep_till(self.cooldown.moderateCooldown)
                        await self.bot.ch.put_queue(self.cmd)

                        self.bot.db.update_cmd_lastran_time("lottery")

            if "You can only bet up to 250,000 cowoncy!" in message.content:
                await self.bot.ch.remove_queue(id="lottery")
                await asyncio.sleep(self.bot.calc_time())
                await self.bot.sleep_till(self.cooldown.moderateCooldown)
                await self.bot.ch.put_queue(self.cmd)

                self.bot.db.update_cmd_lastran_time("lottery")


async def setup(bot):
    await bot.add_cog(Lottery(bot))
