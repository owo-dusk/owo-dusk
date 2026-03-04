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
#from uwu import MyClient


class Owo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.owo_ongoing = False

    @property
    def settings(self):
        return self.bot.settings_dict_temp.commands.owo

    async def send_owo(self, startup=False):
        cmd = {
            "cmd_name": "owo",
            "prefix": False,
            "checks": True,
            "id": "owo",
            "removed": False,
        }
        if not startup:
            await self.bot.remove_queue(id="owo")
            self.owo_ongoing = True
            await self.bot.sleep(self.settings.get_cd())
            self.owo_ongoing = False
        await self.bot.put_queue(cmd, quick=True)

    """gets executed when the cog is first loaded"""

    async def cog_load(self):
        if (
            not self.settings.enabled
            or self.bot.settings_dict_temp.cooldowns.reactionBot.owo
        ):
            try:
                asyncio.create_task(self.bot.unload_cog("cogs.owo"))
            except ExtensionNotLoaded:
                pass
        else:
            asyncio.create_task(self.send_owo(startup=True))

    @commands.Cog.listener()
    async def on_message(self, message):
        if (
            message.channel.id == self.bot.cm.id
            and message.author.id == self.bot.user.id
        ):
            if message.content in {"owo", "uwu"}:
                if not self.owo_ongoing:
                    await self.send_owo()


async def setup(bot):
    await bot.add_cog(Owo(bot))
