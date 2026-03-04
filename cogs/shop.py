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

from discord.ext import commands
from discord.ext.commands import ExtensionNotLoaded
#from uwu import MyClient

"""
SHOP-
100-110 - limited time items
200-274 - wallpapers (one time buy)
1-7 - rings
"""

cash_regex = r"for \*\*(\d+)\*\* <:cowoncy:\d+>"


class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cmd = {
            "cmd_name": "buy",
            "cmd_arguments": "",
            "prefix": True,
            "checks": True,
            "id": "shop",
        }

    @property
    def settings(self):
        return self.bot.settings_dict_temp.commands.shop

    async def cog_load(self):
        if not self.settings.enabled:
            try:
                asyncio.create_task(self.bot.unload_cog("cogs.shop"))
            except ExtensionNotLoaded:
                pass
        else:
            asyncio.create_task(self.send_buy(startup=True))

    async def cog_unload(self):
        await self.bot.remove_queue(id="shop")

    async def send_buy(self, startup=False):
        if startup:
            await self.bot.sleep_till(
                self.bot.settings_dict_temp.cooldowns.shortCooldown
            )
        else:
            await self.bot.remove_queue(id="shop")
            await self.bot.sleep(self.settings.get_cd())

        items_to_buy = self.settings.get_items_to_buy(
            cur_cash=self.bot.user_status["balance"],
            cash_check=self.bot.settings_dict_temp.cashCheck,
        )

        item = self.bot.random.choice(items_to_buy)

        if item:
            self.cmd["cmd_arguments"] = item
            await self.bot.put_queue(self.cmd)
        else:
            await self.send_buy()

    @commands.Cog.listener()
    async def on_message(self, message):
        nick = self.bot.get_nick(message)

        if not message.channel.id == self.bot.cm.id:
            return
        if nick not in message.content:
            return

        if "**, you bought a " in message.content:
            self.bot.update_cash(
                int(re.search(cash_regex, message.content).group(1)), reduce=True
            )
            await self.send_buy()


async def setup(bot):
    await bot.add_cog(Shop(bot))
