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
import json
import re

from discord.ext import commands
from utils.misc import check_list_index
from utils.timestamp import (
    discord_timestamp_to_datetime,
    calc_time_till_event,
    calc_time_till_timestamp,
)
from cogs._BASE import BaseCog

EVENT_REGEX = r"\*\*\|\*\* `\[\d+\/10"

try:
    with open("utils/emojis.json", "r", encoding="utf-8") as file:
        emoji_dict = json.load(file)
except FileNotFoundError:
    print("The file emojis.json was not found.")
except json.JSONDecodeError:
    print("Failed to decode JSON from the file.")


def get_emoji_names(text, emoji_dict=emoji_dict):
    pattern = re.compile(
        r"<a:[a-zA-Z0-9_]+:[0-9]+>|:[a-zA-Z0-9_]+:|[\U0001F300-\U0001F6FF\U0001F700-\U0001F77F]"
    )
    emojis = pattern.findall(text)
    emoji_names = [emoji_dict[char]["name"] for char in emojis if char in emoji_dict]
    return emoji_names


def valid_event_checker(content: str) -> bool:
    months = [
        "jan",
        "feb",
        "mar",
        "apr",
        "may",
        "jun",
        "jul",
        "aug",
        "sep",
        "oct",
        "nov",
        "dec",
    ]
    if not any(month in content for month in months):
        # Month not in message, even message will always have one
        return False

    if "event" not in content:
        # Event message should contain `event` right!
        return False

    # These are flags to increase accuracy but word-work could be changed in future
    # so iam fine with even one of them being in there

    celebration_flag = "celebration" in content
    rewards_flag = "possible rewards" in content
    catch_rates_flag = "catch rates" in content

    if celebration_flag or rewards_flag or catch_rates_flag:
        return True

    return False


class Others(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.zoo = False
        self.lootbox_cmd = {
            "cmd_name": self.bot.alias["lootbox"]["normal"],
            "prefix": True,
            "checks": False,
            "slash_cmd_name": "lootbox",
            "id": "lootbox",
        }

        self.crate_cmd = {
            "cmd_name": self.bot.alias["crate"]["normal"],
            "prefix": True,
            "checks": False,
            "slash_cmd_name": "crate",
            "id": "crate",
        }
        self.event_date_detected = False
        self.bot.message_dispatcher.register(self.on_component_message)

    @property
    def auto_use(self):
        return self.bot.settings_dict.autoUse

    @property
    def webhook_settings(self):
        return self.bot.global_settings_dict.webhook

    @commands.Cog.listener()
    async def on_message(self, message):
        nick = self.bot.get_nick(message)
        if not message.author.id == self.bot.owo_bot_id:
            return

        if message.channel.id == self.bot.cm.id:
            # Accept Rules
            if (
                "**you must accept these rules to use the bot!**"
                in message.content.lower()
            ):
                await asyncio.sleep(self.bot.random.uniform(0.6, 1.7))
                if (
                    message.components[0].children[0]
                    and not message.components[0].children[0].disabled
                ):
                    await message.components[0].children[0].click()

            if (
                nick not in message.content
                and self.bot.user.display_name not in message.content
            ):
                return

            # Cash Check
            if "you currently have **__" in message.content and nick in message.content:
                """task: add checks for cash at ready."""
                self.bot.update_cash(
                    int(
                        re.search(
                            r"(\d{1,3}(?:,\d{3})*)(?= cowoncy)",
                            re.sub(r"[*_]", "", message.content),
                        )
                        .group(0)
                        .replace(",", "")
                    ),
                    override=True,
                )
                await self.bot.log(
                    f"Has {self.bot.user_status['balance']} cowoncy!", "#d787d7"
                )
                if not self.bot.user_status["checked_cash"]:
                    self.bot.user_status["checked_cash"] = True
                await self.bot.remove_queue(id="cash")

            # Lootbox and Crate
            elif (
                "** You received a **weapon crate**!" in message.content
                or "You found a **weapon crate**!" in message.content
            ):
                if self.auto_use.crate:
                    await self.bot.put_queue(self.crate_cmd)

                if self.webhook_settings.enabled and self.webhook_settings.others.crate:
                    await self.bot.send_webhook("crate")

            elif (
                "** You received a **lootbox**!" in message.content
                or "You found a **lootbox**!" in message.content
            ):
                if (
                    self.webhook_settings.enabled
                    and self.webhook_settings.others.lootbox
                ):
                    await self.bot.send_webhook("lootbox")

                if self.auto_use.lootbox:
                    await self.bot.put_queue(self.lootbox_cmd)
                    # give time for command to run
                    await asyncio.sleep(2.5)

            elif "<a:boxopen:427019823747301377> **|** and finds" in message.content:
                # Lootbox opened
                self.bot.user_status["no_gems"] = False

            # Add animals to team
            elif "Create one with `owo team add {animal}`" in message.content:
                await self.bot.set_stat(False)
                self.zoo = True
                team_cmd = {
                    "cmd_name": self.bot.alias["zoo"]["normal"],
                    "prefix": True,
                    "checks": False,
                    "retry_count": 0,
                    "id": "zoo",
                }
                await self.bot.sleep_till(
                    self.bot.settings_dict.cooldowns.shortCooldown
                )
                await self.bot.put_queue(team_cmd, priority=True)

            elif "s zoo! **" in message.content and self.zoo:
                animals = get_emoji_names(message.content)
                animals.reverse()
                await asyncio.sleep(self.bot.random.uniform(1.5, 2.3))
                three_animals = min(len(animals), 3)  # int
                for i in range(three_animals):
                    zoo_cmd = {
                        "cmd_name": "team",
                        "cmd_arguments": f"add {animals[i]}",
                        "prefix": True,
                        "checks": False,
                        "retry_count": 0,
                        "id": "team",
                    }
                    await self.bot.put_queue(zoo_cmd, priority=True)
                    await asyncio.sleep(self.bot.random.uniform(1.5, 2.3))

                self.zoo = False
                await self.bot.set_stat(True)
        if re.search(EVENT_REGEX, message.content):
            # event message detected
            if not self.bot.ongoing_owobot_event:
                await self.bot.log("OwO Event Detected! - DB not updated", "#aeb596")
                self.bot.ongoing_owobot_event = True

        # Battle quest
        if not self.bot.ongoing_battle_external_quest:
            return
        if f"<@{self.bot.user.id}" == message.content:
            if message.embeds and message.embeds[0].footer:
                emb = message.embeds[0]
                if (
                    emb.footer.text.lower()
                    == "this challenge will expire in 10 minutes"
                ):
                    if (
                        message.components[0].children[0]
                        and not message.components[0].children[0].disabled
                    ):
                        await message.components[0].children[0].click()

    async def on_component_message(self, message):
        if self.event_date_detected:
            return

        if not message.author.id == self.bot.owo_bot_id:
            return

        for component in message.components:
            if component.component_name == "text_display":
                content = component.content.lower()
                if not valid_event_checker(content):
                    return
                # First Update status
                if not self.bot.ongoing_owobot_event:
                    await self.bot.log("OwO Event Detected!", "#aeb596")
                self.bot.ongoing_owobot_event = True
                # This is like the life-saver of this!
                # every even message contains this,
                # but again, this can be worded differently in future... ;(
                magic_word = "how long is the event?"
                magic_word_length = len(magic_word)

                if magic_word in content:
                    # Here we would try figure out common patterns to find quest end.

                    # Index where magic word **starts**
                    start_idx = content.index(magic_word)
                    after_magic_word = start_idx + magic_word_length

                    next_45_chars = content[after_magic_word : after_magic_word + 45]

                    # 1. Discord Time stamp
                    # This would be the most accurate approach!
                    timestamp_matches = re.search(r"<t:(\d+):f>", next_45_chars)
                    timestamp = None
                    time_till_event_ends = None
                    if timestamp_matches:
                        timestamp = int(timestamp_matches.group(1))

                        time_till_event_ends = discord_timestamp_to_datetime(timestamp)

                    if not time_till_event_ends:
                        # 2. Day based approach
                        initiated_timestamp = None
                        # Note: we use 1 as index because divider component is ignored
                        # If this doesn't get matched then that would mean there is a pattern change
                        # In announcement command so would need to be reworked based on that...
                        exists, timestamp_component = check_list_index(
                            1, message.components
                        )
                        if (
                            exists
                            and timestamp_component.component_name == "text_display"
                        ):
                            timestamp_matches = re.search(
                                r"<t:(\d+):f>", timestamp_component.content
                            )
                            if timestamp_matches:
                                initiated_timestamp = int(timestamp_matches.group(1))

                        if initiated_timestamp:
                            initiated_datetime = discord_timestamp_to_datetime(
                                initiated_timestamp
                            )
                            # an even typically lasts around 7 days
                            # this approach is less accurate, we may need to rely on when using the gem
                            # causes the message not allowing user to use the special gem
                            # as a fall back.
                            time_till_event_ends = calc_time_till_event(
                                initiated_datetime
                            )

                    # Here UPDATE DATABASE!
                    if time_till_event_ends:
                        self.event_date_detected = True
                        self.bot.db.update_event_timestamp(
                            int(time_till_event_ends.timestamp())
                        )
                        await self.bot.log(
                            f"OwO Event should last till {time_till_event_ends.strftime('%d-%b-%Y %I:%M %p')}",
                            "#aeb596",
                        )
                        # Toggle off
                        seconds_remaining = calc_time_till_timestamp(
                            time_till_event_ends
                        )
                        await asyncio.sleep(max(0, seconds_remaining))
                        await self.bot.log(
                            "Stopping special gem usage, event end time.", "#924444"
                        )
                        self.bot.ongoing_owobot_event = False
                        self.event_date_detected = False


async def setup(bot):
    await bot.add_cog(Others(bot))
