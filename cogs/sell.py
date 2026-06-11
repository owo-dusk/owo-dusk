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
import time

from discord.ext import commands, tasks
from cogs._BASE import BaseCog

"""
TASK:
improve cooldown system (somehow) to make both same.
perhaps make a new category `animals` as we are already handling command being put separately...?
"""


RARITY_MAP = {
    "c": "common",
    "u": "uncommon",
    "r": "rare",
    "e": "epic",
    "s": "special",  # special
    "m": "mythical",
    "g": "gem",
    "l": "legendary",
    "d": "distorted",
    "f": "fabled",
    "h": "hidden",
}


class Sell(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.sell_lastran = 0
        self.sac_lastran = 0
        self.startup = True

    @property
    def animal_setting(self):
        return self.bot.settings_dict.animal

    @property
    def sell_settings(self):
        return self.animal_setting.sell

    @property
    def sac_settings(self):
        return self.animal_setting.sac

    """def allocate_points(self, command: str, rarities: str):
        if command not in ("sell", "sac"):
            raise ValueError("Invalid command name")
            
        rarities_list = rarities.split()
        for item in rarities_list:
            self.__dict__[f"{command}_point"] += POINT_CHART[item]

    def calculate_allocation(self, command: str):
        if command not in ("sell", "sac"):
            raise ValueError("Invalid command name")
        cmds = ["sell", "sac"]
        cmds.pop(command)"""

    def get_cmd_argument(self, cmd):
        arg = getattr(self, f"{cmd}_settings").rarity.get_rarities()
        if self.startup:
            self.startup = False
            return arg

        arg_list = arg.split()
        filtered_items = [
            item
            for item in arg_list
            if (rarity := RARITY_MAP[item]) and self.bot.animal_rank_in_zoo[rarity]
            # https://www.geeksforgeeks.org/python/walrus-operator-in-python-3-8/
        ]
        arg = " ".join(filtered_items).strip()
        if arg != "":
            return " ".join(filtered_items)
        return None

    def get_command(self, name: str):
        if name not in ("sell", "sac"):
            raise ValueError("Invalid command name")

        arg = self.get_cmd_argument(name)
        if not arg:
            return None

        base = {
            "cmd_name": name,
            "cmd_arguments": arg,
            "prefix": True,
            "checks": True,
            "id": name,
        }
        return base

    def get_last_ran(self):
        return "sell" if self.sell_lastran <= self.sac_lastran else "sac"

    @tasks.loop()
    async def initiate_loop(self):
        choices = ["sell", "sac"]
        self.bot.random.shuffle(choices)
        for cmd in choices:
            if not getattr(self, f"{cmd}_settings").enabled:
                # skip disabled ones
                continue
            last_ran = self.__dict__[f"{cmd}_lastran"]
            cd = self.animal_setting.get_cd()
            gap = time.monotonic() - last_ran
            if last_ran == 0 or gap > cd:
                cmd_data = self.get_command(cmd)
                if cmd_data:
                    await self.bot.sleep_till([10, 15])
                    await self.bot.put_queue(cmd_data)
                    self.__dict__[f"{cmd}_lastran"] = time.monotonic()

        await self.bot.sleep_till([10, 15])

    async def cog_load(self):
        # start loop, cog will stay awake due to the necessity to calculate value
        self.initiate_loop.start()

    async def cog_unload(self):
        # this shouldn't get removed since its supposed to run.
        await self.bot.remove_queue(id="sell")
        await self.bot.remove_queue(id="sac")

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

                if self.bot.settings_dict.cashCheck:
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
                await self.bot.remove_queue(id="sac")

            elif "you don't have enough animals! >:c" in message.content.lower():
                # May want to improve this later..
                await self.bot.remove_queue(id=self.get_last_ran())


async def setup(bot):
    await bot.add_cog(Sell(bot))
