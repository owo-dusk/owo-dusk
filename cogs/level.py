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
import string
import random

from discord.ext import commands
from discord.ext.commands import ExtensionNotLoaded
#from uwu import MyClient


quotes_url = "https://favqs.com/api/qotd"


def generate_random_string(min, max):
    """something like a list?"""
    characters = string.ascii_lowercase + " "
    length = random.randint(min, max)
    random_string = "".join(random.choice(characters) for _ in range(length))
    return random_string


async def fetch_quotes(session):
    async with session.get(quotes_url) as response:
        if response.status == 200:
            data = await response.json()
            # quote = data["quote"]["body"]
            if data.get("quote"):
                return data["quote"].get("body", None)


class Level(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_level_grind_message = None
        self.cmd = {"cmd_name": None, "prefix": False, "checks": True, "id": "level"}

    @property
    def settings(self):
        return self.bot.settings_dict_temp.commands.lvlGrind

    async def start_level_grind(self):
        # await asyncio.sleep(1)
        await self.bot.remove_queue(id="level")
        try:
            await self.bot.sleep(self.settings.get_cd())
            if self.settings.useQuote:
                self.last_level_grind_message = await fetch_quotes(self.bot.session)
                if not self.last_level_grind_message:
                    await self.bot.log(
                        "Error - start_level_grind: Fetching quotes failed, using a random string of text instead.",
                        "#c25560",
                    )
                    self.last_level_grind_message = generate_random_string(
                        self.settings.minLength, self.settings.maxLength
                    )
            else:
                self.last_level_grind_message = generate_random_string(
                    self.settings.minLength, self.settings.maxLength
                )
            self.cmd["cmd_name"] = self.last_level_grind_message

            await self.bot.put_queue(self.cmd)
        except Exception as e:
            await self.bot.log(f"Error - start_level_grind(): {e}", "#c25560")

    """gets executed when the cog is first loaded"""

    async def cog_load(self):
        if not self.settings.enabled:
            try:
                asyncio.create_task(self.bot.unload_cog("cogs.level"))
            except ExtensionNotLoaded:
                pass
        else:
            asyncio.create_task(self.start_level_grind())

    async def cog_unload(self):
        await self.bot.remove_queue(id="level")

    @commands.Cog.listener()
    async def on_message(self, message):
        if (
            message.channel.id == self.bot.cm.id
            and message.author.id == self.bot.user.id
        ):
            if self.last_level_grind_message == message.content:
                await self.start_level_grind()


async def setup(bot):
    await bot.add_cog(Level(bot))
