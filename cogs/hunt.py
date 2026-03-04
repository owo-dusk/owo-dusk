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
from discord.ext.commands import ExtensionNotLoaded
#from uwu import MyClient


try:
    with open("utils/emojis.json", "r", encoding="utf-8") as file:
        emoji_dict = json.load(file)
except FileNotFoundError:
    print("The file emojis.json was not found.")
except json.JSONDecodeError:
    print("Failed to decode JSON from the file.")


def get_emoji_cost(text, emoji_dict=emoji_dict):
    pattern = re.compile(
        r"<a:[a-zA-Z0-9_]+:[0-9]+>|:[a-zA-Z0-9_]+:|[\U0001F300-\U0001F6FF\U0001F700-\U0001F77F]"
    )
    emojis = pattern.findall(text)
    emoji_names = [
        emoji_dict[char]["sell_price"] for char in emojis if char in emoji_dict
    ]
    return emoji_names


def get_emoji_values(text):
    emoji_costs = get_emoji_cost(text)
    total_sell_price = 0

    for sell_price in emoji_costs:
        total_sell_price += sell_price

    return total_sell_price


class Hunt(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cmd = {
            "cmd_name": "",
            "prefix": True,
            "checks": True,
            "id": "hunt",
            "slash_cmd_name": "hunt",
            "removed": False,
        }
        self.was_recently_disabled = False

    @property
    def settings(self):
        return self.bot.settings_dict_temp.commands.hunt

    def get_emoji_tier(self, text, emoji_dict=emoji_dict):
        # https://emojiapi.dev/api/v1/lady_beetle/100.png
        pattern = re.compile(
            r"<a:[a-zA-Z0-9_]+:[0-9]+>|:[a-zA-Z0-9_]+:|[\U0001F300-\U0001F6FF\U0001F700-\U0001F77F]"
        )
        emojis = pattern.findall(text)

        result_list = []

        rank_map = {
            "common": (1, "<:common:416520037713838081>"),
            "uncommon": (2, "<:uncommon:416520056269176842>"),
            "rare": (3, "<:rare:416520066629107712>"),
            "epic": (4, "<:epic:416520722987614208>"),
            "mythical": (5, "<:mythic:416520808501084162>"),
            "gem": (6, "<a:gem:510023576489951232> "),
            "legendary": (7, "<a:legendary:417955061801680909>"),
            "fabled": (8, "<a:fabled:438857004493307907>"),
            "hidden": (9, "<a:hidden:459203677438083074>"),
        }
        highest_rank = {"rarity": "", "emoji": ""}

        for emoji in emojis:
            emoji_data = emoji_dict.get(emoji)

            if emoji_data:
                if self.bot.global_settings_dict["webhook"]["animal_log"]["rank"][
                    emoji_data["rank"]
                ]:
                    if emoji.startswith("<a:"):
                        emoji_id = emoji[3:-1]
                        url = f"https://cdn.discordapp.com/emojis/{emoji_id}.gif"
                    else:
                        emoji_id = emoji[1:-1]
                        if "2" in emoji_id:
                            # quick work-around to discord adding 2 at end of emoji names
                            # I guess this should fix invalid id error for all required emojies
                            emoji_id = emoji_id[:-1]
                        url = f"https://emojiapi.dev/api/v1/{emoji_id}/100.png"

                    result_list.append(
                        {
                            # "name": emoji_id,
                            "rank": emoji_data["rank"],
                            "emoji_url": url,
                            "emoji": emoji,
                        }
                    )
                    if (
                        rank_map[emoji_data["rank"]][0]
                        > rank_map.get(highest_rank["rarity"], (0, ""))[0]
                    ):
                        highest_rank["rarity"] = emoji_data["rank"]
                        highest_rank["emoji"] = rank_map[emoji_data["rank"]][1]

        return result_list, highest_rank

    async def cog_load(self):
        if (
            not self.settings.enabled
            or self.bot.settings_dict_temp.cooldowns.reactionBot.huntAndBattle
        ):
            try:
                asyncio.create_task(self.bot.unload_cog("cogs.hunt"))
            except ExtensionNotLoaded:
                pass
        else:
            self.cmd["cmd_name"] = (
                self.bot.alias["hunt"]["shortform"]
                if self.settings.shortform
                else self.bot.alias["hunt"]["normal"]
            )
            asyncio.create_task(self.bot.put_queue(self.cmd))

    async def cog_unload(self):
        await self.bot.remove_queue(id="hunt")

    @commands.Cog.listener()
    async def on_message(self, message):
        nick = self.bot.get_nick(message)
        if nick not in message.content:
            return

        if self.bot.hunt_disabled:
            # Ensure hunt is currently not in queue
            if not self.was_recently_disabled:
                await self.bot.remove_queue(id="hunt")
                self.was_recently_disabled = True
            return
        elif self.was_recently_disabled:
            self.was_recently_disabled = False
            self.cmd["cmd_name"] = (
                self.bot.alias["hunt"]["shortform"]
                if self.settings.shortform
                else self.bot.alias["hunt"]["normal"]
            )
            await self.bot.put_queue(self.cmd)

        if (
            message.channel.id == self.bot.cm.id
            and message.author.id == self.bot.owo_bot_id
        ):
            if (
                "you found:" in message.content.lower()
                or "caught" in message.content.lower()
            ):
                await self.bot.remove_queue(id="hunt")

                msg_lines = message.content.splitlines()
                msg_line = (
                    msg_lines[0]
                    if "caught" in message.content.lower()
                    else msg_lines[1]
                )

                sell_value = get_emoji_values(msg_line)
                # Wait why are reducing 5 again when we are alrady reducing that from sell val? checkk
                self.bot.update_cash(sell_value - 5, assumed=True)
                self.bot.update_cash(5, reduce=True)

                if (
                    self.bot.global_settings_dict["webhook"]["enabled"]
                    and self.bot.global_settings_dict["webhook"]["animal_log"][
                        "enabled"
                    ]
                ):
                    result_list, highest_rank = self.get_emoji_tier(msg_line)
                    if result_list:
                        if len(result_list) > 1:
                            description = f"User: <@{self.bot.user.id}> caught the following pets:\n> "
                            for item in result_list:
                                description += f"{item['emoji']} "
                            # Multiple items, compact mode.
                            description += f"\n-# Best catch: {highest_rank['emoji']} {highest_rank['rarity']}"
                            await self.bot.webhookSender(
                                title="Caught multiple animals from hunt!",
                                desc=description,
                                colors="#5B0B74",
                                author_name="Hunt",
                                author_img_url="https://cdn.discordapp.com/emojis/633448858432831488.gif",
                            )
                        else:
                            await self.bot.webhookSender(
                                title=f"Caught {highest_rank['emoji']} {result_list[0]['emoji']} from hunt!",
                                desc=f"> User: <@{self.bot.user.id}> caught a(an) {result_list[0]['rank']} {result_list[0]['emoji']}.",
                                colors="#5B0B74",
                                img_url=result_list[0]["emoji_url"],
                            )

                await self.bot.sleep(self.settings.get_cd())
                self.cmd["cmd_name"] = (
                    self.bot.alias["hunt"]["shortform"]
                    if self.settings.shortform
                    else self.bot.alias["hunt"]["normal"]
                )
                await self.bot.put_queue(self.cmd)


async def setup(bot):
    await bot.add_cog(Hunt(bot))
