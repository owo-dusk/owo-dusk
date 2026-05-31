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

import re
import asyncio

from discord.ext import commands
from discord.ext.commands import ExtensionNotLoaded
from cogs._BASE import BaseCog

"""
TASK:
improve cooldown system (somehow) to make both same.
perhaps make a new category `animals` as we are already handling command being put seperately...?
"""


class Sell(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)

        self.sell_cmd = {
            "cmd_name": "sell",
            "cmd_arguments": "",
            "prefix": True,
            "checks": True,
            "id": "sell",
        }

        self.sac_cmd = {
            "cmd_name": self.bot.alias["sac"]["normal"],
            "cmd_arguments": "",
            "prefix": True,
            "checks": True,
            "id": "sell",
        }

    def fetch_arguments(self, cmd):
        return " ".join(self.bot.settings_dict["commands"][cmd]["rarity"])

    async def sell_sac_queue(self, cmd, cooldown):
        await self.bot.sleep_till(cooldown)
        cmd["cmd_arguments"] = self.fetch_arguments(cmd["cmd_name"])
        await self.bot.put_queue(cmd)

    async def cog_load(self):
        if (
            not self.bot.settings_dict["commands"]["sell"]["enabled"]
            and not self.bot.settings_dict["commands"]["sac"]["enabled"]
        ):
            try:
                asyncio.create_task(self.bot.unload_cog("cogs.sell"))
            except ExtensionNotLoaded:
                pass
        else:
            if (
                self.bot.settings_dict["commands"]["sell"]["enabled"]
                and self.bot.settings_dict["commands"]["sac"]["enabled"]
            ) or (self.bot.settings_dict["commands"]["sell"]["enabled"]):
                # start sell first.
                asyncio.create_task(
                    self.sell_sac_queue(
                        self.sell_cmd,
                        self.bot.settings_dict["commands"]["sell"]["cooldown"],
                    )
                )
            else:
                asyncio.create_task(
                    self.sell_sac_queue(
                        self.sac_cmd,
                        self.bot.settings_dict["commands"]["sac"]["cooldown"],
                    )
                )

    async def cog_unload(self):
        await self.bot.remove_queue(id="sell")

    @commands.Cog.listener()
    async def on_message(self, message):
        nick = self.bot.get_nick(message)
        if nick not in message.content:
            return

        if (
            message.channel.id == self.bot.cm.id
            and message.author.id == self.bot.owo_bot_id
        ):
            if (
                "for a total of **<:cowoncy:416043450337853441>"
                in message.content.lower()
            ):
                await self.bot.remove_queue(id="sell")

                if self.bot.settings_dict["cashCheck"]:
                    try:
                        self.bot.update_cash(
                            int(
                                re.search(
                                    r"for a total of \*\*<:cowoncy:\d+> ([\d,]+)",
                                    message.content,
                                )
                                .group(1)
                                .replace(",", "")
                            )
                        )
                    except Exception:
                        await self.bot.log(
                            "failed to fetch cowoncy from sales", "#af0087"
                        )

                if self.bot.settings_dict["commands"]["sac"]["enabled"]:
                    await self.sell_sac_queue(
                        self.sac_cmd,
                        self.bot.settings_dict["commands"]["sac"]["cooldown"],
                    )
                else:
                    await self.sell_sac_queue(
                        self.sell_cmd,
                        self.bot.settings_dict["commands"]["sell"]["cooldown"],
                    )

            elif (
                "sacrificed" in message.content
                and "for a total of" in message.content.lower()
            ):
                await self.bot.remove_queue(id="sell")
                if self.bot.settings_dict["commands"]["sell"]["enabled"]:
                    await self.sell_sac_queue(
                        self.sell_cmd,
                        self.bot.settings_dict["commands"]["sell"]["cooldown"],
                    )
                else:
                    await self.sell_sac_queue(
                        self.sac_cmd,
                        self.bot.settings_dict["commands"]["sac"]["cooldown"],
                    )
            elif "you don't have enough animals! >:c" in message.content.lower():
                await self.bot.remove_queue(id="sell")


async def setup(bot):
    await bot.add_cog(Sell(bot))
