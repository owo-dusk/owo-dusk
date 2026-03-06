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

from utils.notification import notify
#from uwu import MyClient


won_pattern = r"you won \*\*<:cowoncy:\d+> ([\d,]+)"
lose_pattern = r"spent \*\*<:cowoncy:\d+> ([\d,]+)"


class Coinflip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cmd = {
            "cmd_name": self.bot.alias["coinflip"]["normal"],
            "cmd_arguments": None,
            "prefix": True,
            "checks": True,
            "id": "coinflip",
        }
        self.turns_lost = 0
        self.exceeded_max_amount = False

        self.gamble_flags = {
            "goal_reached": False,
            "amount_exceeded": False,
            "no_balance": False,
        }

    @property
    def gamble_settings(self):
        return self.bot.settings_dict_temp.gamble

    @property
    def settings(self):
        return self.bot.settings_dict_temp.gamble.coinflip

    @property
    def cooldowns(self):
        return self.bot.settings_dict_temp.cooldowns

    async def cog_load(self):
        if not self.settings.enabled:
            try:
                asyncio.create_task(self.bot.unload_cog("cogs.coinflip"))
            except ExtensionNotLoaded as e:
                print(e)
            except Exception as e:
                print(e)
        else:
            asyncio.create_task(self.start_cf(startup=True))

    async def cog_unload(self):
        await self.bot.remove_queue(id="coinflip")

    async def start_cf(self, startup=False):
        goal_system = self.gamble_settings.goals
        try:
            if startup:
                await self.bot.sleep_till(self.cooldowns.briefCooldown)
            else:
                await self.bot.remove_queue(id="coinflip")
                await self.bot.sleep_till(self.settings.get_cd())

            amount_to_gamble = int(
                self.settings.startValue * (self.settings.multiplier**self.turns_lost)
            )

            # Goal system check
            if goal_system.enabled and self.bot.gain_or_lose > goal_system.amount:
                if not self.gamble_flags["goal_reached"]:
                    self.gamble_flags["goal_reached"] = True
                    await self.bot.log(
                        f"goal reached - {self.bot.gain_or_lose}/{goal_system.amount}, stopping coinflip!",
                        "#4a270c",
                    )
                    notify(
                        f"goal reached - {self.bot.gain_or_lose}/{goal_system.amount}, stopping coinflip!",
                        "Coinflip - Goal reached",
                    )

                await self.bot.sleep_till(self.cooldowns.moderateCooldown)
                return await self.start_cf()
            elif self.gamble_flags["goal_reached"]:
                self.gamble_flags["goal_reached"] = False

            # Balance check
            if (
                amount_to_gamble > self.bot.user_status["balance"]
                and self.bot.user_status["checked_cash"]
            ):
                if not self.gamble_flags["no_balance"]:
                    self.gamble_flags["no_balance"] = True
                    await self.bot.log(
                        f"Amount to gamle next ({amount_to_gamble}) exceeds bot balance ({self.bot.user_status['balance']}), stopping coinflip!",
                        "#4a270c",
                    )
                    notify(
                        f"Amount to gamle next ({amount_to_gamble}) exceeds bot balance ({self.bot.user_status['balance']}), stopping coinflip!",
                        "Coinflip - Insufficient balance",
                    )

                await self.bot.sleep_till(self.cooldowns.moderateCooldown)
                return await self.start_cf()
            elif self.gamble_flags["no_balance"]:
                await self.bot.log(
                    f"Balance regained! ({self.bot.user_status['balance']}) - restarting coinflip!",
                    "#4a270c",
                )
                self.gamble_flags["no_balance"] = False

            # Allotted value check
            allottedAmount = self.gamble_settings.allottedAmount
            if self.bot.gain_or_lose + (allottedAmount - amount_to_gamble) <= 0:
                if not self.gamble_flags["amount_exceeded"]:
                    self.gamble_flags["amount_exceeded"] = True
                    await self.bot.log(
                        f"Allotted value ({allottedAmount}) exceeded, stopping coinflip!",
                        "#4a270c",
                    )
                    notify(
                        f"Alloted value ({allottedAmount}) exceeded, stopping coinflip!",
                        "Coinflip - Alloted value exceeded",
                    )

                await self.bot.sleep_till(self.cooldowns.moderateCooldown)
                return await self.start_cf()
            elif self.gamble_flags["amount_exceeded"]:
                self.gamble_flags["amount_exceeded"] = False

            if amount_to_gamble > 250000:
                await self.bot.log(
                    f"Value to gamble ({amount_to_gamble}) exceeded 250k threshhold, stopping coinflip!",
                    "#4a270c",
                )
                notify(
                    f"Value to gamble ({amount_to_gamble}) exceeded 250k threshhold, stopping coinflip!",
                    "Coinflip - Exceeded 250k limit",
                )
                self.exceeded_max_amount = True
            else:
                self.cmd["cmd_arguments"] = str(amount_to_gamble)
                option = self.settings.options.random_choice()

                if option == "h":
                    option = ""

                self.cmd["cmd_arguments"] += f" {option}".rstrip()
                await self.bot.put_queue(self.cmd)

        except Exception as e:
            await self.bot.log(f"Error - {e}, During coinflip start_cf()", "#c25560")

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.id != 408785106942164992:
            return
        if before.channel.id != self.bot.channel_id:
            return
        if self.exceeded_max_amount:
            return

        nick = self.bot.get_nick(before)

        if nick not in after.content:
            return

        if "chose" in after.content.lower():
            try:
                if "and you lost it all... :c" in after.content.lower():
                    self.turns_lost += 1
                    match = int(
                        re.search(lose_pattern, after.content).group(1).replace(",", "")
                    )

                    self.bot.update_cash(match, reduce=True)
                    self.bot.gain_or_lose -= match

                    await self.bot.log(
                        f"lost {match} in cf, net profit - {self.bot.gain_or_lose}",
                        "#993f3f",
                    )
                    await self.start_cf()
                    self.bot.update_gamble_db("losses")
                else:
                    won_match = int(
                        re.search(won_pattern, after.content).group(1).replace(",", "")
                    )
                    lose_match = int(
                        re.search(lose_pattern, after.content).group(1).replace(",", "")
                    )
                    self.turns_lost = 0
                    profit = won_match - lose_match

                    self.bot.update_cash(profit)
                    self.bot.gain_or_lose += profit

                    await self.bot.log(
                        f"won {won_match} in cf, net profit - {self.bot.gain_or_lose}",
                        "#536448",
                    )
                    await self.start_cf()
                    self.bot.update_gamble_db("wins")
            except Exception as e:
                await self.bot.log(
                    f"Error - {e}, During coinflip on_message_edit()", "#c25560"
                )


async def setup(bot):
    await bot.add_cog(Coinflip(bot))

