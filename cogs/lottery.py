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

from discord.ext import commands
from discord.ext.commands import ExtensionNotLoaded
#from uwu import MyClient


def load_json_dict(file_path="utils/stats.json"):
    with open(file_path, "r") as config_file:
        return json.load(config_file)


lock = threading.Lock()


def load_dict():
    global accounts_dict
    accounts_dict = load_json_dict()


load_dict()


class Lottery(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self._cmd = {
            "cmd_name": self.bot.alias["lottery"]["normal"],
            "cmd_arguments": 0,
            "prefix": True,
            "checks": True,
            "id": "lottery",
        }

    @property
    def cooldown(self):
        return self.bot.settings_dict_temp.cooldowns

    @property
    def settings(self):
        return self.bot.settings_dict_temp.commands.lottery

    @property
    def cmd(self):
        self._cmd["cmd_argument"] = self.settings.amount
        return self._cmd

    async def start_lottery(self):
        if str(self.bot.user.id) in accounts_dict:
            last_lottery_time = accounts_dict[str(self.bot.user.id)].get("lottery", 0)

            if not self.bot.should_run(last_lottery_time):
                await asyncio.sleep(
                    self.bot.calc_time()
                )  # Wait until next 12:00 AM PST

            await self.bot.sleep_till(self.cooldown.shortCooldown)
            await self.bot.put_queue(self.cmd)

            with lock:
                load_dict()
                accounts_dict[str(self.bot.user.id)]["lottery"] = (
                    self.bot.time_in_seconds()
                )
                with open("utils/stats.json", "w") as f:
                    json.dump(accounts_dict, f, indent=4)

    async def cog_load(self):
        if not self.bot.settings.enabled:
            try:
                asyncio.create_task(self.bot.unload_cog("cogs.lottery"))
            except ExtensionNotLoaded:
                pass
        else:
            asyncio.create_task(self.start_lottery())

    async def cog_unload(self):
        await self.bot.remove_queue(id="lottery")

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
                        await self.bot.remove_queue(id="lottery")
                        await asyncio.sleep(self.bot.calc_time())
                        await self.bot.sleep_till(self.cooldown.moderateCooldown)
                        await self.bot.put_queue(self.cmd)
                        with lock:
                            load_dict()
                            accounts_dict[str(self.bot.user.id)]["lottery"] = (
                                self.bot.time_in_seconds()
                            )
                            with open("utils/stats.json", "w") as f:
                                json.dump(accounts_dict, f, indent=4)

            if "You can only bet up to 250,000 cowoncy!" in message.content:
                await self.bot.remove_queue(id="lottery")
                await asyncio.sleep(self.bot.calc_time())
                await self.bot.sleep_till(self.cooldown.moderateCooldown)
                await self.bot.put_queue(self.cmd)
                with lock:
                    load_dict()
                    accounts_dict[str(self.bot.user.id)]["lottery"] = (
                        self.bot.time_in_seconds()
                    )
                    with open("utils/stats.json", "w") as f:
                        json.dump(accounts_dict, f, indent=4)


async def setup(bot):
    await bot.add_cog(Lottery(bot))
