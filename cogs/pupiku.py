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
        self.completed_today = set()
        self.tomorrow_tasks = {}

    @property
    def pup_settings(self):
        return self.bot.settings_dict_temp.commands.pup

    @property
    def piku_settings(self):
        return self.bot.settings_dict_temp.commands.piku

    def enabled_commands(self):
        cmds = []
        if self.pup_settings.enabled:
            cmds.append("pup")
        if self.piku_settings.enabled:
            cmds.append("piku")
        return cmds

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

    async def mark_complete_today(self, cmd_name: str):
        self.completed_today.add(cmd_name)
        self.bot.db.update_cmd_lastran_time(cmd_name)
        await self.bot.remove_queue(id=cmd_name)

        task = self.tomorrow_tasks.pop(cmd_name, None)
        if task and not task.done():
            task.cancel()
        self.tomorrow_tasks[cmd_name] = asyncio.create_task(
            self.resume_tomorrow(cmd_name)
        )

    async def resume_tomorrow(self, cmd_name: str):
        await asyncio.sleep(self.bot.calc_time())
        self.completed_today.discard(cmd_name)
        await self.send_pupiku(cmd=cmd_name, initial=True)

    def detect_command_result(self, content: str):
        if "Your garden is out of carrots!" in content:
            return "piku", True
        if "There are no puppies to adopt!" in content:
            return "pup", True
        if "You picked one PikPik carrot" in content:
            return "piku", "today!" in content
        if "You picked up one puppy" in content:
            return "pup", "today!" in content
        return "", False

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
        for task in self.tomorrow_tasks.values():
            if not task.done():
                task.cancel()

    async def send_pupiku(
        self, startup=False, cmd=None, final=False, initial=False, initial_delay=0
    ):
        if startup:
            await self.bot.sleep_till(
                self.bot.settings_dict_temp.cooldowns.shortCooldown
            )
            cmds = self.enabled_commands()
            self.bot.random.shuffle(cmds)

            delay = 0
            for index, cmd_name in enumerate(cmds):
                if index:
                    delay += self.bot.random.uniform(1, 3)
                asyncio.create_task(
                    self.send_pupiku(
                        cmd=cmd_name, initial=True, initial_delay=delay
                    )
                )
        else:
            if cmd not in self.enabled_commands():
                return
            if cmd in self.completed_today:
                return

            if initial_delay:
                await asyncio.sleep(initial_delay)
            if cmd in self.completed_today:
                return

            if initial:
                last_ran = await self.bot.db.fetch_cmd_lastran_time(cmd)
                if not self.bot.should_run(last_ran):
                    self.completed_today.add(cmd)
                    self.tomorrow_tasks[cmd] = asyncio.create_task(
                        self.resume_tomorrow(cmd)
                    )
                    return
            else:
                await self.bot.remove_queue(id=cmd)
                if final:
                    await self.mark_complete_today(cmd)
                    return
                else:
                    await self.bot.sleep(getattr(self, f"{cmd}_settings").get_cd())
                    if cmd in self.completed_today:
                        return

            self.set_send_time(cmd)
            await self.bot.put_queue(self.__dict__[f"{cmd}_cmd"])


    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.channel.id == self.bot.cm.id:
            return

        if message.author.id != self.bot.owo_bot_id:
            return

        detected_cmd, detected_final = self.detect_command_result(message.content)
        if detected_cmd:
            if detected_cmd not in self.enabled_commands():
                return
            if detected_final:
                await self.mark_complete_today(detected_cmd)
                return
            if self.set_and_validate_resp_time(detected_cmd):
                await self.send_pupiku(cmd=detected_cmd, final=detected_final)
            return



        


async def setup(bot):
    await bot.add_cog(Pupiku(bot))
