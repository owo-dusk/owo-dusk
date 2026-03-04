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
import time

from discord.ext import commands
from discord.ext.commands import ExtensionNotLoaded
#from uwu import MyClient


def compare_with_timestamp(timestamp, last_ran_time):
    if last_ran_time <= timestamp:
        # Probably have not joined giveaway
        return True
    else:
        # Already must have joined giveaway
        return False


class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def cooldowns(self):
        return self.bot.settings_dict_temp.cooldowns

    @property
    def settings(self):
        return self.bot.settings_dict_temp.giveaway

    """Join previous giveaways"""
    async def join_previous_giveaways(self):
        prev_time = await self.bot.fetch_giveaway_db()

        await self.bot.sleep_till(self.cooldowns.shortCooldown)
        await self.bot.wait_until_ready()

        # Using briefcooldown here as using the long cooldown of giveaway joiner might look weird here.
        await self.bot.sleep_till(self.cooldowns.briefCooldown)
        for chnl in self.settings.channels:
            try:
                channel = await self.bot.fetch_channel(chnl)
            except Exception:
                channel = None
            if not channel:
                # To prevent giving error if channel id is invalid
                await self.bot.log(
                    f"giveaway channel id -> {chnl} seems to be invalid", "#ff5f00"
                )
                continue
            await self.bot.set_stat(False)
            async for message in channel.history(
                limit=self.settings.messageRangeToCheck
            ):
                if message.embeds:
                    for embed in message.embeds:
                        if (
                            embed.author.name is not None
                            and " A New Giveaway Appeared!" in embed.author.name
                            and message.channel.id in self.settings.channels
                        ):
                            if not prev_time or (
                                prev_time
                                and compare_with_timestamp(
                                    message.created_at.timestamp(), prev_time
                                )
                            ):
                                await self.bot.sleep_till(self.cooldowns.briefCooldown)
                                if (
                                    message.components[0].children[0]
                                    and not message.components[0].children[0].disabled
                                ):
                                    await message.components[0].children[0].click()
                                    await self.bot.log(
                                        f"giveaway joined in {message.channel.name}",
                                        "#00d7af",
                                    )

            await self.bot.set_stat(True)
        # Set prev_time for future use
        self.bot.update_giveaway_db(time.time())

    """gets executed when the cog is first loaded"""

    async def cog_load(self):
        if self.settings.enabled:
            """Run join_previous_giveaways when bot is ready"""
            asyncio.create_task(self.join_previous_giveaways())
        else:
            try:
                asyncio.create_task(self.bot.unload_cog("cogs.giveaway"))
            except ExtensionNotLoaded:
                pass

    @commands.Cog.listener()
    async def on_message(self, message):
        """Join Giveaways"""
        if message.channel.id in self.settings.channels:
            if message.embeds:
                for embed in message.embeds:
                    if (
                        embed.author.name is not None
                        and " A New Giveaway Appeared!" in embed.author.name
                        and message.channel.id in self.settings.channels
                    ):
                        prev_time = await self.bot.fetch_giveaway_db()
                        if not prev_time or (
                            prev_time
                            and compare_with_timestamp(
                                message.created_at.timestamp(), prev_time
                            )
                        ):
                            await self.bot.sleep(self.settings.get_cd())
                            if (
                                message.components[0].children[0]
                                and not message.components[0].children[0].disabled
                            ):
                                await message.components[0].children[0].click()
                                await self.bot.log(
                                    f"giveaway joined in {message.channel.name}",
                                    "#00d7af",
                                )


async def setup(bot):
    await bot.add_cog(Giveaway(bot))
