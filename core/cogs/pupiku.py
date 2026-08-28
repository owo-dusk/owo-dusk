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
import time

from discord.ext import commands
from discord.ext.commands import ExtensionNotLoaded

from core.cogs._BASE import BaseCog


def done_running(times_ran, times_to_run):
    # if times_to_run is 0, that means we run indefinitely till failure message to determine next day's count
    return (times_ran >= times_to_run) and not times_to_run == 0


class Pupiku(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)

        self.startupFinished = False
        self.command_status = {
            "pup": {
                "command_send_time": 0,
                "command_resp_time": 0,
                "times_ran": 0,
                "force_break": False,
                "should_run": 0,
            },
            "piku": {
                "command_send_time": 0,
                "command_resp_time": 0,
                "times_ran": 0,
                "force_break": False,
                "should_run": 0,
            },
            "run": {
                "command_send_time": 0,
                "command_resp_time": 0,
                "times_ran": 0,
                "force_break": False,
                "should_run": 0,
            },
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

    @property
    def run_settings(self):
        return self.bot.settings_dict.commands.run

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
        if not (
            self.pup_settings.enabled
            or self.piku_settings.enabled
            or self.run_settings.enabled
        ):
            try:
                asyncio.create_task(self.bot.unload_cog("core.cogs.pupiku"))
            except ExtensionNotLoaded:
                pass
        else:
            asyncio.create_task(self.send_pupiku(startup=True))

    async def cog_unload(self):
        for cmd in {"pup", "piku", "run"}:
            await self.bot.ch.remove_queue(id=cmd)

    async def send_pupiku(self, cmd=None, startup=False, final=False):
        if startup and not final:
            while not self.startupFinished:
                await self.bot.sleep_till(
                    self.bot.settings_dict.cooldowns.shortCooldown
                )
                cmds = ["pup", "piku", "run"]
                self.bot.random.shuffle(cmds)

                for cmd in cmds:
                    # Initial setup:
                    if not getattr(self, f"{cmd}_settings").enabled:
                        continue

                    # Ensure command not ran for the day
                    last_ran = await self.bot.db.fetch_pupiku_lastran_time(cmd)
                    if not self.bot.should_run(last_ran):
                        await self.send_pupiku(cmd=cmd, startup=True, final=True)
                        continue

                    # Set `should_run`
                    self.command_status[cmd][
                        "should_run"
                    ] = await self.bot.db.check_next_amt_to_run(cmd)

                    self.set_send_time(cmd)
                    await self.bot.ch.put_queue(self.get_cmd(cmd))
                    await self.bot.sleep_till([1, 3])

                # Incase of failure during initial start
                # once one command is successful, this isn't an issue.
                await self.bot.sleep(60)
        else:
            await self.bot.ch.remove_queue(id=cmd)
            cd = getattr(self, f"{cmd}_settings").get_cd()

            # Command ran successfully till end.
            if final:
                cd += self.bot.calc_time()
                self.bot.db.update_pupiku_lastran_time(cmd)

                if not startup:
                    times_ran = self.command_status[cmd]["times_ran"]
                    if not self.command_status[cmd]["force_break"]:
                        # Command was not stopped from final message.
                        times_ran += 1

                    self.bot.db.update_pupiku_times_to_run(cmd, times_ran)

                    # Reset previous states:
                    self.command_status[cmd]["times_ran"] = 0
                    self.command_status[cmd]["should_run"] = 0
                    self.command_status[cmd]["force_break"] = False

            await self.bot.sleep(cd)
            self.set_send_time(cmd)
            await self.bot.ch.put_queue(self.get_cmd(cmd))

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.channel.id == self.bot.cm.id:
            return

        if message.author.id == self.bot.user.id:
            if f"{self.bot.settings_dict.prefix}pup" in message.content:
                self.set_send_time("pup")
            if f"{self.bot.settings_dict.prefix}piku" in message.content:
                self.set_send_time("piku")
            if f"{self.bot.settings_dict.prefix}run" in message.content:
                self.set_send_time("run")

        if message.author.id != self.bot.owo_bot_id:
            return

        final = False
        cmd = ""
        if "You picked one PikPik carrot" in message.content:
            cmd = "piku"
        elif "You picked up one puppy" in message.content:
            cmd = "pup"
        elif "kilometers today!" in message.content:
            cmd = "run"

        if cmd and self.set_and_validate_resp_time(cmd):
            self.command_status[cmd]["times_ran"] += 1
            if done_running(
                self.command_status[cmd]["times_ran"],
                self.command_status[cmd]["should_run"],
            ):
                final = True
            print(f"{self.bot.user.name} - re-queued {cmd}")
            self.startupFinished = True
            await self.send_pupiku(cmd=cmd, final=final)
            return
        elif cmd:
            print(f"{self.bot.user.name} - failed re-queue {cmd}")

        # Command forcefully stopped.
        cmd = ""
        if "🚫 **|** Your garden is out of carrots!" in message.content:
            cmd = "piku"
        elif "🚫 **|** There are no puppies to adopt!" in message.content:
            cmd = "pup"
        elif "🚫 **|** You are too tired to run!" in message.content:
            cmd = "run"

        if cmd and self.set_and_validate_resp_time(cmd):
            match = re.search(r"(\d+)(?: \w+)? tomorrow!", message.content)
            # command may have been ran and done in previous session
            self.startupFinished = True
            final = True

            if match:
                self.command_status[cmd]["times_ran"] = int(match.group(1))

            self.command_status[cmd]["force_break"] = True
            print(f"{self.bot.user.name} - done with {cmd}")
            await self.send_pupiku(cmd=cmd, final=final)


async def setup(bot):
    await bot.add_cog(Pupiku(bot))
