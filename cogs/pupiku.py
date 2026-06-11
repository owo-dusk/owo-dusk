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

from discord.ext import commands
from discord.ext.commands import ExtensionNotLoaded
from cogs._BASE import BaseCog


class Pupiku(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)

        self.startupFinished = False
        self.command_status = {
            "pup": {"command_send_time": 0, "command_resp_time": 0},
            "piku": {"command_send_time": 0, "command_resp_time": 0},
        }

    def get_cmd(self, cmd_name: str):
        # NOTE: Here we are using separate id's
        base = {
            "cmd_name": cmd_name,
            "prefix": True,
            "checks": self.startupFinished,
            "id": cmd_name,
        }
        return base

    @property
    def pup_settings(self):
        return self.bot.settings_dict.commands.pup

    @property
    def piku_settings(self):
        return self.bot.settings_dict.commands.piku

    def set_and_validate_resp_time(self, cmd_name: str):
        resp_time = time.monotonic()

        # 1. Ensure send time is set and is not 0
        if not self.command_status[cmd_name]["command_send_time"]:
            print("send time is 0 or not set")
            return False

        # 2. Make sure last respond isn't within 60 seconds
        if self.command_status[cmd_name]["command_resp_time"]:
            time_gap = resp_time - self.command_status[cmd_name]["command_resp_time"]
            if time_gap < 60:
                return False

        # 3. Check if resp time is within 10s~ of send time
        time_gap = resp_time - self.command_status[cmd_name]["command_send_time"]
        if time_gap < 0 or time_gap > 10:
            return False

        self.command_status[cmd_name]["command_resp_time"] = resp_time
        return True

    def set_send_time(self, cmd_name: str):
        self.command_status[cmd_name]["command_send_time"] = time.monotonic()

    async def cog_load(self):
        if not (self.pup_settings.enabled or self.piku_settings.enabled):
            try:
                asyncio.create_task(self.bot.unload_cog("cogs.pupiku"))
            except ExtensionNotLoaded:
                pass
        else:
            asyncio.create_task(self.send_pupiku(startup=True))

    async def cog_unload(self):
        await self.bot.remove_queue(id="pup")
        await self.bot.remove_queue(id="piku")

    async def send_pupiku(self, startup=False, cmd=None, final=False):
        if startup:
            while not self.startupFinished:
                await self.bot.sleep_till(
                    self.bot.settings_dict.cooldowns.shortCooldown
                )
                cmds = ["pup", "piku"]
                choice = self.bot.random.choice(cmds)
                cmds.remove(choice)

                await self.bot.put_queue(self.get_cmd(choice))
                await self.bot.sleep_till([1, 3])
                await self.bot.put_queue(self.get_cmd(cmds[0]))
                # Incase of failure during initial start
                # once one command is successful, this isn't an issue.
                await self.bot.sleep(60)
        else:
            await self.bot.remove_queue(id=cmd)
            cd = getattr(self, f"{cmd}_settings").get_cd()
            if final:
                cd += self.bot.calc_time()
            await self.bot.sleep(cd)
            self.set_send_time(cmd)
            await self.bot.put_queue(self.get_cmd(cmd))

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.channel.id == self.bot.cm.id:
            return

        if message.author.id == self.bot.user.id:
            if f"{self.bot.settings_dict.prefix}pup" in message.content:
                self.set_send_time("pup")
            if f"{self.bot.settings_dict.prefix}piku" in message.content:
                self.set_send_time("piku")

        if message.author.id != self.bot.owo_bot_id:
            return

        final = False
        cmd = ""
        if "You picked one PikPik carrot" in message.content:
            cmd = "piku"
        elif "You picked up one puppy" in message.content:
            cmd = "pup"
        if "today!" in message.content:
            # its a weird method, but the `!` at the end always exists
            # when the day's total pup/piku is ran. A solid way to detect finish!
            final = True

        if cmd and self.set_and_validate_resp_time(cmd):
            print(f"{self.bot.user.name} - re-queued {cmd}")
            self.startupFinished = True
            await self.send_pupiku(cmd=cmd, final=final)
            return
        else:
            print(f"{self.bot.user.name} - failed re-queue {cmd}")

        cmd = ""
        if "🚫 **|** Your garden is out of carrots!" in message.content:
            cmd = "piku"
        elif "🚫 **|** There are no puppies to adopt!" in message.content:
            cmd = "pup"

        if cmd and self.set_and_validate_resp_time(cmd):
            # command may have been ran and done in previous session
            self.startupFinished = True
            print(f"{self.bot.user.name} - done with {cmd}")
            await self.send_pupiku(cmd=cmd, final=final)


async def setup(bot):
    await bot.add_cog(Pupiku(bot))
