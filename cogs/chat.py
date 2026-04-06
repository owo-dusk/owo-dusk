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

from discord.ext import commands


class Chat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def settings(self):
        return self.bot.global_settings_dict.textCommands

    @commands.Cog.listener()
    async def on_message(self, message):
        if (
            message.author.id
            in [self.bot.user.id, 1209017744696279041] + self.settings.allowedUsers
        ):
            if (
                f"{self.settings.prefix}{self.settings.stopCommand}"
                in message.content.lower()
            ):
                await self.bot.log(
                    "stopping owo-dusk.. Please be warned that this sometimes doesn't work as expected. Please don't rely on it much.",
                    "#87875f",
                )
                self.bot.command_handler_status["sleep"] = True

            elif (
                f"{self.settings.prefix}{self.settings.startCommand}"
                in message.content.lower()
            ):
                await self.bot.log("starting owo-dusk..", "#87875f")
                self.bot.command_handler_status["sleep"] = False

        if (
            f"{self.settings.prefix}{self.settings.restartCommand}"
            in message.content.lower()
        ):
            await self.bot.log("restarting owo-dusk after captcha", "#87875f")
            self.bot.command_handler_status["captcha"] = False


async def setup(bot):
    await bot.add_cog(Chat(bot))
