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

import json
import asyncio
import threading
import re

from discord.ext import commands
from discord.ext.commands import ExtensionNotLoaded
from cogs._BASE import BaseCog


def load_json_dict(file_path="utils/stats.json"):
    with open(file_path, "r", encoding="utf-8") as config_file:
        return json.load(config_file)


cmd = {"cmd_name": "daily", "prefix": True, "checks": True, "id": "daily"}

lock = threading.Lock()


def load_dict():
    global accounts_dict
    accounts_dict = load_json_dict()


load_dict()


class Daily(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)

    @property
    def cooldowns(self):
        return self.bot.settings_dict.cooldowns

    async def start_daily(self):
        if str(self.bot.user.id) in accounts_dict:
            last_daily_time = accounts_dict[str(self.bot.user.id)].get("daily", 0)

            if not self.bot.should_run(
                last_daily_time
            ):  # 86400 = seconds till a day(24hrs).
                await asyncio.sleep(
                    self.bot.calc_time()
                )  # Wait until next 12:00 AM PST

            await self.bot.sleep_till(self.cooldowns.briefCooldown)
            await self.bot.put_queue(cmd, priority=True)
            await self.bot.set_stat(False)

            with lock:
                load_dict()
                accounts_dict[str(self.bot.user.id)]["daily"] = (
                    self.bot.time_in_seconds()
                )
                with open("utils/stats.json", "w", encoding="utf-8") as f:
                    json.dump(accounts_dict, f, indent=4)

    async def cog_load(self):
        if not self.bot.settings_dict.daily:
            try:
                asyncio.create_task(self.bot.unload_cog("cogs.daily"))
            except ExtensionNotLoaded:
                pass
        else:
            asyncio.create_task(self.start_daily())

    async def cog_unload(self):
        await self.bot.remove_queue(id="daily")

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
                await self.bot.remove_queue(cmd)
                await self.bot.set_stat(True)
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
                await self.bot.put_queue(cmd, priority=True)
                await self.bot.set_stat(False)
                with lock:
                    load_dict()
                    accounts_dict[str(self.bot.user.id)]["daily"] = (
                        self.bot.time_in_seconds()
                    )
                    with open("utils/stats.json", "w", encoding="utf-8") as f:
                        json.dump(accounts_dict, f, indent=4)

                if self.bot.global_settings_dict.webhook.enabled:
                    await self.bot.send_webhook("daily_claim")

            if (
                "**⏱ |** Nu! **" in message.content
                and "! You need to wait" in message.content
            ):
                await self.bot.remove_queue(cmd)
                await self.bot.set_stat(True)
                await asyncio.sleep(self.bot.calc_time())
                await self.bot.sleep_till(self.cooldowns.moderateCooldown)
                await self.bot.put_queue(cmd, priority=True)
                await self.bot.set_stat(False)
                with lock:
                    load_dict()
                    accounts_dict[str(self.bot.user.id)]["daily"] = (
                        self.bot.time_in_seconds()
                    )
                    with open("utils/stats.json", "w", encoding="utf-8") as f:
                        json.dump(accounts_dict, f, indent=4)


async def setup(bot):
    await bot.add_cog(Daily(bot))
