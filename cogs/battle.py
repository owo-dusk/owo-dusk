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
from utils.notification import notify
from cogs._BASE import BaseCog


class Battle(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.cmd = {
            "cmd_name": "",
            "prefix": True,
            "checks": True,
            "id": "battle",
            "slash_cmd_name": "battle",
            "removed": False,
            "channel": None,
            "cmd_arguments": None,
        }

    @property
    def settings(self):
        return self.bot.settings_dict.commands.battle

    async def cog_load(self):
        if (
            not self.settings.enabled
            or self.bot.settings_dict.cooldowns.reactionBot.huntAndBattle
        ):
            try:
                asyncio.create_task(self.bot.unload_cog("cogs.battle"))
            except Exception:
                pass
        else:
            self.cmd["cmd_name"] = (
                self.bot.alias["battle"]["shortform"]
                if self.settings.shortform
                else self.bot.alias["battle"]["normal"]
            )
            asyncio.create_task(self.bot.put_queue(self.cmd))

    async def cog_unload(self):
        await self.bot.remove_queue(id="battle")

    @commands.Cog.listener()
    async def on_message(self, message):
        try:
            if (
                message.channel.id == self.bot.cm.id
                and message.author.id == self.bot.owo_bot_id
            ):
                if message.embeds:
                    for embed in message.embeds:
                        if (
                            embed.author.name is not None
                            and f"{self.bot.user.display_name} goes into battle!"
                            in embed.author.name
                        ):
                            if embed.footer:
                                if self.settings.show_streak:
                                    await self.bot.log(
                                        f"{embed.footer.text}", "#292252"
                                    )
                                if "You lost in " in embed.footer.text:
                                    if self.settings.notify_streak_loss:
                                        notify(
                                            embed.footer.text, "You lost your streak!"
                                        )
                            if message.reference is not None:
                                """Return if embed"""
                                referenced_message = (
                                    await message.channel.fetch_message(
                                        message.reference.message_id
                                    )
                                )

                                if (
                                    not referenced_message.embeds
                                    and "You found a **weapon crate**!"
                                    in referenced_message.content
                                ):
                                    # Ignore reply and proceeding!
                                    pass
                                else:
                                    # Return from battle embed reply
                                    return

                            await self.bot.remove_queue(id="battle")
                            await self.bot.sleep(self.settings.get_cd())
                            self.cmd["cmd_name"] = (
                                self.bot.alias["battle"]["shortform"]
                                if self.settings.shortform
                                else self.bot.alias["battle"]["normal"]
                            )
                            await self.bot.put_queue(self.cmd)

            cnf = self.bot.quest_help_request["battle"]
            if not cnf["enabled"]:
                return

            if f"<@{cnf['userid']}" == message.content:
                emb = message.embeds[0] if message.embeds else None
                if not emb:
                    return
                if (
                    emb.author.name is not None
                    and self.bot.user.display_name in emb.author.name
                ):
                    if (
                        emb.footer.text.lower()
                        == "this challenge will expire in 10 minutes"
                    ):
                        await self.bot.remove_queue(id="battle")
                        self.bot.quest_help_request["battle"]["till"] -= 1
                        (
                            current,
                            completed,
                        ) = await self.bot.quest_handler.qh.update_progress(
                            self.bot.user.id, cnf["userid"], "battle_friend"
                        )
                        if current is not None:
                            await self.bot.quest_handler.sync_progress(
                                "battle_friend", current, completed
                            )

                        if (
                            completed
                            or self.bot.quest_help_request["battle"]["till"] <= 0
                        ):
                            # reset
                            self.bot.quest_help_request["battle"] = {
                                "till": 0,
                                "enabled": False,
                                "userid": 0,
                                "channel": 0,
                            }

        except Exception as e:
            await self.bot.log(f"Error - {e}, During battle on_message()", "#c25560")


async def setup(bot):
    await bot.add_cog(Battle(bot))
