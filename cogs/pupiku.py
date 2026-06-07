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

        # NOTE: Here we are using seperate id's
        self.pup_cmd = {
            "cmd_name": "pup",
            "prefix": True,
            "checks": True,
            "id": "pup",
        }

        self.piku_cmd = {
            "cmd_name": "piku",
            "prefix": True,
            "checks": True,
            "id": "piku",
        }

        self.command_status = {
            "pup": {"command_send_time": 0, "command_resp_time": 0},
            "piku": {"command_send_time": 0, "command_resp_time": 0},
        }

    @property
    def pup_settings(self):
        return self.bot.settings_dict_temp.commands.pup

    @property
    def piku_settings(self):
        return self.bot.settings_dict_temp.commands.piku

    def set_and_validate_resp_time(self, cmd_name: str):
        # 1. set resp time
        resp_time = time.monotonic()
        # 2. ensure send time is set and is not 0
        if not self.command_status[cmd_name]["command_send_time"]:
            print("send time is 0 or not set")
            return False
        # 3. ensure time gap isn't within 60s
        if self.command_status[cmd_name]["command_resp_time"]:
            # In case resp time is 0 then the logic would assume all first runs are invalid
            time_gap = resp_time - self.command_status[cmd_name]["command_resp_time"]
            if time_gap < 60:
                # The minumum cooldown of Pup and Piku command would be 60.
                return False
        # After time gap is calculated, modify command_resp_time
        self.command_status[cmd_name]["command_resp_time"] = resp_time

        # 4. Check if resp time is around within 10~ s
        time_gap = resp_time - self.command_status[cmd_name]["command_send_time"]
        if time_gap < 0 or time_gap > 10:
            return False

        # If all above checks are invalid, then it is likely a valid responce
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
            asyncio.create_task(self.send_buy(send_pupiku=True))

    async def cog_unload(self):
        await self.bot.remove_queue(id="pup")
        await self.bot.remove_queue(id="piku")

    async def send_pupiku(self, startup=False, cmd=None, final=False):
        if startup:
            await self.bot.sleep_till(
                self.bot.settings_dict_temp.cooldowns.shortCooldown
            )
            cmds = ["pup", "piku"]
            choice = self.bot.random.choice(cmds)
            cmds.remove(choice)

            await self.bot.put_queue(self.__dict__[f"{choice}_cmd"])
            await self.bot.sleep_till([1,3])
            await self.bot.put_queue(self.__dict__[f"{cmds[0]}_cmd"])
        else:
            await self.bot.remove_queue(id=cmd)
            cd = self.__dict__[f"{cmd}_settings"].get_cd()
            if final:
                cd+=self.bot.calc_time()
            await self.bot.sleep(cd)
            self.set_send_time(cmd)
            await self.bot.put_queue(self.__dict__[f"{cmd}_cmd"])


    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.channel.id == self.bot.cm.id:
            return

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
            await self.send_pupiku(cmd=cmd, final=final)
            return

        cmd = ""
        if "🚫 **|** Your garden is out of carrots!" in message.content:
            cmd = "piku"
        elif "🚫 **|** There are no puppies to adopt!" in message.content:
            cmd = "pup"

        if cmd and self.set_and_validate_resp_time(cmd):
            # command may have been ran and done in previous session
            await self.send_pupiku(cmd=cmd, final=final)


        


async def setup(bot):
    await bot.add_cog(Pupiku(bot))
