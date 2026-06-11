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
import time
import re

from discord.ext import commands
from discord.ext.commands import ExtensionNotLoaded
from cogs._BASE import BaseCog

ARMY_REGEX = r"Today's remaining Broken Army Emblem : (\d+)"


class Army(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)

        self.cmd = {
            "cmd_name": "army",
            "prefix": True,
            "checks": True,
            "id": "army",
        }

        self.command_status = {"command_send_time": 0, "command_resp_time": 0}

    async def cog_load(self):
        if not self.settings.enabled:
            try:
                asyncio.create_task(self.bot.unload_cog("cogs.army"))
            except ExtensionNotLoaded:
                pass
        else:
            asyncio.create_task(self.send_army(startup=True))

    async def cog_unload(self):
        await self.bot.remove_queue(id="army")

    @property
    def settings(self):
        return self.bot.settings_dict.commands.army

    def set_send_time(self):
        self.command_status["command_send_time"] = time.monotonic()

    def set_and_validate_resp_time(self):
        resp_time = time.monotonic()

        # 1. Ensure send time is set and is not 0
        if not self.command_status["command_send_time"]:
            print("send time is 0 or not set")
            return False

        # 2. Make sure last respond isn't within 60 seconds
        if self.command_status["command_resp_time"]:
            time_gap = resp_time - self.command_status["command_resp_time"]
            if time_gap < 60:
                return False

        # 3. Check if resp time is within 10s~ of send time
        time_gap = resp_time - self.command_status["command_send_time"]
        if time_gap < 0 or time_gap > 10:
            return False

        self.command_status["command_resp_time"] = resp_time
        return True

    async def send_army(self, startup=False, finished=False):
        if startup:
            # Check existing time:
            last_ran = await self.bot.db.fetch_cmd_lastran_time("army")
            if not self.bot.should_run(last_ran):
                await asyncio.sleep(self.bot.calc_time())
            await self.bot.sleep_till(self.bot.settings_dict.cooldowns.shortCooldown)
        else:
            await self.bot.remove_queue(id="army")
            await self.bot.sleep(self.settings.get_cd())

        if finished:
            # set time to today's
            self.bot.db.update_cmd_lastran_time("army")
            await asyncio.sleep(self.bot.calc_time())

        # I know we do update from on_message but for safety
        self.set_send_time()
        await self.bot.put_queue(self.cmd)

    @commands.Cog.listener()
    async def on_message(self, message):
        nick = self.bot.get_nick(message)
        if not message.channel.id == self.bot.cm.id:
            return

        if message.author.id not in [self.bot.user.id, self.bot.owo_bot_id]:
            return

        if (
            message.author.id == self.bot.user.id
            and f"{self.bot.settings_dict.prefix}army" in message.content
        ):
            self.set_send_time()

        if message.author.id == self.bot.owo_bot_id:
            if "Today's remaining Broken Army Emblem" in message.content:
                if self.set_and_validate_resp_time():
                    # Iam tired...
                    value = int(re.search(ARMY_REGEX, message.content).group(1))
                    if not value > 0:
                        await self.send_army(finished=True)
                    else:
                        print(value)
                        await self.send_army()

            if (
                f"**🚫 | {nick}**, you can only find 15 emblems per day!"
                in message.content
            ):
                # remove command from queue
                await self.bot.remove_queue(id="army")
                # update, sleep
                self.bot.db.update_cmd_lastran_time("army")
                await asyncio.sleep(self.bot.calc_time())
                # re run
                await self.send_army()


async def setup(bot):
    await bot.add_cog(Army(bot))
