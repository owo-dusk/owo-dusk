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

from discord.ext import commands, tasks
from discord.ext.commands import ExtensionNotLoaded


class ChannelSwitcher(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Temporary
        self.default_channel_id = self.bot.channel_id

    @tasks.loop()
    async def switch_channel_loop(self):
        await self.bot.sleep_till(
            self.bot.global_settings_dict["channelSwitcher"]["interval"]
        )
        status, resp = await self.change_channel()

        if not status:
            await self.bot.log(f"Error - {resp}", "#c25560")
        else:
            await self.bot.log(f"Channel switcher: {resp}", "#9dc3f5")

    async def change_channel(self):
        cnf = self.bot.global_settings_dict["channelSwitcher"]
        current_channel_id = self.bot.cm.id

        item = None
        for entry in cnf["users"]:
            if entry["userid"] == self.bot.user.id:
                item = entry
                break

        available_channels = item["channels"] if item else []
        available_channels+cnf["allUsers"]["channels"]
        valid_channels = [
            cid for cid in available_channels if cid != current_channel_id
        ]
        # Converts to set (no repitations)
        valid_channels = set(valid_channels)

        # Temporary
        if self.default_channel_id not in valid_channels:
            valid_channels.append(self.default_channel_id)

        while valid_channels:
            channel_id = self.bot.random.choice(valid_channels)
            try:
                new_channel = await self.bot.fetch_channel(channel_id)
                if new_channel:
                    await self.bot.empty_checks_and_switch(new_channel)
                    return (
                        True,
                        f"Switched successfully to channel {new_channel.name}",
                    )
            except Exception as e:
                await self.bot.log(
                    f"Error - Failed to fetch channel with id {channel_id}: {e}",
                    "#c25560",
                )

            valid_channels.remove(channel_id)
        return False, "Failed to switch channel - No active channels found."


    async def cog_load(self):
        if not self.bot.global_settings_dict["channelSwitcher"]["enabled"]:
            try:
                asyncio.create_task(self.bot.unload_cog("cogs.channelSwitcher"))
            except ExtensionNotLoaded:
                pass
        else:
            self.switch_channel_loop.start()

    async def cog_unload(self):
        self.switch_channel_loop.cancel()


async def setup(bot):
    await bot.add_cog(ChannelSwitcher(bot))

