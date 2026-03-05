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
#from uwu import MyClient


class Battle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cmd = {
            "cmd_name": "",
            "prefix": True,
            "checks": True,
            "id": "battle",
            "slash_cmd_name": "battle",
            "removed": False,
        }

    @property
    def settings(self):
        return self.bot.settings_dict_temp.commands.battle

    async def cog_load(self):
        if (
            not self.settings.enabled
            or self.bot.settings_dict_temp.cooldowns.reactionBot.huntAndBattle
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
                            await self.bot.sleep(
                                self.settings.get_cd()
                            )
                            self.cmd["cmd_name"] = (
                                self.bot.alias["battle"]["shortform"]
                                if self.settings.shortform
                                else self.bot.alias["battle"]["normal"]
                            )
                            await self.bot.put_queue(self.cmd)
        except Exception as e:
            await self.bot.log(f"Error - {e}, During battle on_message()", "#c25560")


async def setup(bot):
    await bot.add_cog(Battle(bot))
