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
import time
import heapq

from discord.ext import commands, tasks
from cogs._BASE import BaseCog

"""
TASK:
improve cooldown system (somehow) to make both same.
perhaps make a new category `animals` as we are already handling command being put seperately...?
"""

"""
Calculation of point_chart:
(2 * sell_value + sac_value) / (sell_value + sac_value)
"""
POINT_CHART = {
    "c": 1,
    "u": 4,
    "r": 13,
    "e": 250,
    "s": 5454,  # special
    "m": 3750,
    "g": 24000,  # gem
    "l": 12000,
    "d": 240000,
    "f": 142857,
    "h": 666666,
}


def get_command(name: str):
    if name not in ("sell", "sac"):
        raise ValueError("Invalid command name")

    base = {
        "cmd_name": name,
        "cmd_arguments": "",
        "prefix": True,
        "checks": True,
        "id": "sell",
    }
    return base


class Sell(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.sell_point = 0
        self.sac_point = 0

    @property
    def sell_settings(self):
        self.bot.settings_dict_temp.animal.sell

    @property
    def sac_settings(self):
        self.bot.settings_dict_temp.animal.sac

    def allocate_points(self, command: str, rarities: str):
        if command not in ("sell", "sac"):
            raise ValueError("Invalid command name")
            
        rarities_list = rarities.split()
        for item in rarities_list:
            self.__dict__[f"{command}_point"] += POINT_CHART[item]

    def calculate_allocation(self, command: str):
        if command not in ("sell", "sac"):
            raise ValueError("Invalid command name")
        cmds = ["sell", "sac"]
        cmds.pop(command)


    @tasks.loop()
    async def initiate_loop(self):
        await self.bot.sleep(10)
        


    async def cog_load(self):
        # start loop, cog will stay awake due to the necessity to calculate value
        pass

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

                if self.bot.settings_dict_temp.cashCheck:
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

            elif (
                "sacrificed" in message.content
                and "for a total of" in message.content.lower()
            ):
                await self.bot.remove_queue(id="sell")

            elif "you don't have enough animals! >:c" in message.content.lower():
                await self.bot.remove_queue(id="sell")


async def setup(bot):
    await bot.add_cog(Sell(bot))
