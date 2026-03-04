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

from discord.ext import commands, tasks
from discord.ext.commands import ExtensionNotLoaded
#from uwu import MyClient


class CustomCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cmd_tracker = []

    def search_cmd_tracker(self, cmd):
        matches = []
        for idx, cmd_data in enumerate(self.cmd_tracker):
            if cmd_data["base"] == cmd:
                matches.append({"index": idx, "data": cmd_data})

        return matches

    def fetch_last_ran_diff(self, last_ran, cooldown):
        # Checks if command can be ran or not.
        if last_ran != 0:
            cd = time.monotonic() - last_ran
            return {"required": cd > cooldown, "cooldown": cd}
        else:
            return {"required": False, "cooldown": 0}

    async def run_cmd(self, cmd_data, tracker_idx=None):
        cmd = {
            "cmd_name": cmd_data.command,
            "prefix": False,
            "checks": False,
            "id": "customcommand",
            "removed": False,
        }

        await self.bot.put_queue(cmd)

        if tracker_idx is not None:
            self.cmd_tracker[tracker_idx]["last_ran"] = time.monotonic()
        else:
            self.cmd_tracker.append({"base": cmd_data, "last_ran": time.monotonic()})

    @property
    def settings(self):
        return self.bot.settings_dict_temp.customCommands

    @tasks.loop()
    async def command_handler(self):
        cd = self.settings.approximate_minimum_cooldown()

        for cmd in self.settings.commands:
            if not cmd.enabled:
                continue

            results = self.search_cmd_tracker(cmd)
            if not results:
                await self.run_cmd(cmd)
            else:
                cd_info_dict = self.fetch_last_ran_diff(
                    results[0]["data"]["last_ran"], cmd.cooldown
                )
                if cd_info_dict["required"]:
                    await self.run_cmd(cmd, results[0]["index"])

                if len(results) != 1:
                    # multiple data detected
                    pass

        await asyncio.sleep(cd)

    async def cog_load(self):
        if not self.settings.enabled:
            try:
                asyncio.create_task(self.bot.unload_cog("cogs.customcommands"))
            except ExtensionNotLoaded:
                pass
        else:
            self.command_handler.start()

    async def cog_unload(self):
        self.command_handler.cancel()


async def setup(bot):
    await bot.add_cog(CustomCommands(bot))
