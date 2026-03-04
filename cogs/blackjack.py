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

from utils.notification import notify
#from uwu import MyClient


def find_optimal_move(e_hand, u_hand, soft=False):
    if e_hand <= 6:
        if soft:
            return "hit" if u_hand < 18 else "stand"
        else:
            if u_hand <= 11:
                return "hit"
            if u_hand == 12:
                return "hit" if e_hand == 2 else "stand"
            return "stand"
    else:
        if soft:
            if u_hand == 18:
                return "hit" if e_hand >= 9 else "stand"
            return "hit" if u_hand < 19 else "stand"
        else:
            return "hit" if u_hand < 17 else "stand"


def fetch_bj_hands(embed):
    dealer_field_name = embed.fields[0].name if len(embed.fields) > 0 else None
    field_name = embed.fields[1].name if len(embed.fields) > 1 else None

    if dealer_field_name and field_name:
        soft = True if "*" in field_name else False
        dealer_card_num = int(re.search(r"\d+", dealer_field_name).group(0))
        card_num = int(re.search(r"\d+", field_name).group(0))
        return {"soft": soft, "dealer": dealer_card_num, "our": card_num}

    else:
        return None


class Blackjack(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.game_event = asyncio.Event()

        self.cmd = {
            "cmd_name": "bj",  # TASK: Shortform handle via config
            "cmd_arguments": None,
            "prefix": True,
            "checks": True,
            "id": "blackjack",
            "removed": False,
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
        return self.bot.settings_dict_temp.gamble.blackjack

    @property
    def cooldowns(self):
        return self.bot.settings_dict_temp.cooldowns

    async def send_blackjack(self, startup=False):
        goal_system = self.gamble_settings.goals

        if startup:
            await self.bot.sleep_till(self.cooldowns.briefCooldown)
        else:
            await self.bot.sleep(self.settings.get_cd())

        amount_to_gamble = int(
            self.settings.startValue * (self.settings.multiplier**self.turns_lost)
        )

        if goal_system.enabled and self.bot.gain_or_lose > goal_system.amount:
            if not self.gamble_flags["goal_reached"]:
                self.gamble_flags["goal_reached"] = True
                await self.bot.log(
                    f"goal reached - {self.bot.gain_or_lose}/{goal_system.amount}, stopping blackjack!",
                    "#4a270c",
                )
                notify(
                    f"goal reached - {self.bot.gain_or_lose}/{goal_system.amount}, stopping blackjack!",
                    "blackjack - Goal reached",
                )

            await self.bot.sleep_till(self.cooldowns.moderateCooldown)
            return await self.send_blackjack()
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
                    f"Amount to gamle next ({amount_to_gamble}) exceeds bot balance ({self.bot.user_status['balance']}), stopping blackjack!",
                    "#4a270c",
                )
                notify(
                    f"Amount to gamle next ({amount_to_gamble}) exceeds bot balance ({self.bot.user_status['balance']}), stopping blackjack!",
                    "blackjack - Insufficient balance",
                )

            await self.bot.sleep_till(self.cooldowns.moderateCooldown)
            return await self.send_blackjack()
        elif self.gamble_flags["no_balance"]:
            await self.bot.log(
                f"Balance regained! ({self.bot.user_status['balance']}) - restarting blackjack!",
                "#4a270c",
            )
            self.gamble_flags["no_balance"] = False

        allottedAmount = self.gamble_settings.allottedAmount
        if self.bot.gain_or_lose + (allottedAmount - amount_to_gamble) <= 0:
            if not self.gamble_flags["amount_exceeded"]:
                self.gamble_flags["amount_exceeded"] = True
                await self.bot.log(
                    f"Allotted value ({allottedAmount}) exceeded, stopping blackjack!",
                    "#4a270c",
                )
                notify(
                    f"Alloted value ({allottedAmount}) exceeded, stopping blackjack!",
                    "blackjack - Alloted value exceeded",
                )

            await self.bot.sleep_till(self.cooldowns.moderateCooldown)
            return await self.send_blackjack()
        elif self.gamble_flags["amount_exceeded"]:
            self.gamble_flags["amount_exceeded"] = False

        if amount_to_gamble > 250000:
            await self.bot.log(
                f"Value to gamble ({amount_to_gamble}) exceeded 250k threshhold, stopping blackjack!",
                "#4a270c",
            )
            notify(
                f"Value to gamble ({amount_to_gamble}) exceeded 250k threshhold, stopping blackjack!",
                "blackjack - Exceeded 250k limit",
            )
            self.exceeded_max_amount = True
        else:
            self.cmd["cmd_arguments"] = str(amount_to_gamble)
            await self.bot.put_queue(self.cmd)

    async def wait_for_bj_edit(self):
        while not self.click_registered:
            await asyncio.sleep(0.1)

    async def click_reaction(self, msg, move):
        cur_emoji = "👊" if move == "hit" else "🛑"
        not_clicked = True
        tries = 0

        while not_clicked:
            await asyncio.sleep(1.5)
            if msg.reactions:
                for item in msg.reactions:
                    if item.emoji == cur_emoji:
                        if item.me:
                            await msg.remove_reaction(cur_emoji, self.bot.user)
                        else:
                            await msg.add_reaction(cur_emoji)
                        not_clicked = False
                        break
            tries += 1
            if tries >= 3:
                return await self.send_blackjack()

        try:
            await asyncio.wait_for(self.game_event.wait(), timeout=4.0)
            self.game_event.clear()
        except asyncio.TimeoutError:
            self.game_event.clear()
            await self.send_blackjack()

    async def cog_load(self):
        if not self.bot.settings_dict_temp.gamble.blackjack.enabled:
            try:
                asyncio.create_task(self.bot.unload_cog("cogs.blackjack"))
            except ExtensionNotLoaded as e:
                print(e)
            except Exception as e:
                print(e)
        else:
            asyncio.create_task(self.send_blackjack(startup=True))

    @commands.Cog.listener()
    async def on_message(self, message):
        if (
            message.channel.id == self.bot.cm.id
            and message.author.id == self.bot.owo_bot_id
        ):
            if message.embeds:
                if (
                    message.embeds[0].author.name is None
                    or self.bot.user.name not in message.embeds[0].author.name
                ):
                    return
                for embed in message.embeds:
                    if embed.footer and any(
                        item in embed.footer.text
                        for item in [
                            "🎲 ~ game in progress",
                            "🎲 ~ resuming previous game",
                        ]
                    ):
                        await self.bot.remove_queue(id="blackjack")
                        # Handle Blackjack.
                        res = fetch_bj_hands(embed)
                        if not res:
                            return

                        optimal_move = find_optimal_move(
                            res["dealer"], res["our"], res["soft"]
                        )
                        await self.click_reaction(message, optimal_move)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if (
            before.channel.id == self.bot.cm.id
            and before.author.id == self.bot.owo_bot_id
        ):
            if after.embeds:
                if (
                    after.embeds[0].author.name is None
                    or self.bot.user.name not in after.embeds[0].author.name
                ):
                    return
                for embed in after.embeds:
                    if embed.footer:
                        if "🎲 ~ game in progress" in embed.footer.text:
                            self.game_event.set()
                            await self.bot.remove_queue(id="blackjack")
                            res = fetch_bj_hands(embed)
                            if not res:
                                return

                            optimal_move = find_optimal_move(
                                res["dealer"], res["our"], res["soft"]
                            )

                            await self.click_reaction(before, optimal_move)

                        elif "🎲 ~ You lost" in embed.footer.text:
                            self.game_event.set()
                            lost_amt = int(
                                re.search(r"([\d,]+)", embed.footer.text)
                                .group(0)
                                .replace(",", "")
                            )

                            self.bot.update_cash(lost_amt, reduce=True)
                            self.bot.gain_or_lose -= lost_amt
                            self.turns_lost += 1

                            await self.bot.log(
                                f"lost {lost_amt} in bj, net profit - {self.bot.gain_or_lose}",
                                "#993f3f",
                            )
                            await self.send_blackjack()
                            self.bot.update_gamble_db("losses")

                        elif "🎲 ~ You won" in embed.footer.text:
                            self.game_event.set()
                            self.turns_lost = 0
                            win_amt = int(
                                re.search(r"([\d,]+)", embed.footer.text)
                                .group(0)
                                .replace(",", "")
                            )

                            self.bot.update_cash(win_amt)
                            self.bot.gain_or_lose += win_amt

                            await self.bot.log(
                                f"won {win_amt} in bj, net profit - {self.bot.gain_or_lose}",
                                "#536448",
                            )
                            await self.send_blackjack()
                            self.bot.update_gamble_db("wins")
                        elif any(
                            item in embed.footer.text
                            for item in ["🎲 ~ You tied!", "🎲 ~ You both bust!"]
                        ):
                            self.game_event.set()
                            await self.bot.log(
                                "didn't win or lose blackjack..", "#ffafaf"
                            )
                            await self.send_blackjack()


async def setup(bot):
    await bot.add_cog(Blackjack(bot))
