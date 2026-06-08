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
from cogs._BASE import BaseCog


class Chat(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.timed_task = None  # track active timed task so we can cancel it

    @property
    def settings(self):
        return self.bot.global_settings_dict.textCommands

    def parse_seconds(self, text: str):
        """
        parse a duration string from the end of a command
        supports plain seconds (30) or suffixed (30s, 2m, 1h)
        returns float seconds or None if not parseable
        """
        text = text.strip()
        if not text:
            return None
        try:
            multipliers = {"s": 1, "m": 60, "h": 3600}
            if text[-1].lower() in multipliers:
                return float(text[:-1]) * multipliers[text[-1].lower()]
            return float(text)
        except ValueError:
            return None

    async def timed_reverse(self, seconds: float):
        # sleep then reverse the bot state
        await asyncio.sleep(seconds)
        self.bot.command_handler_status["sleep"] = False
        await self.bot.log(
            "Sleep complete — starting owo-dusk.",
            "#87875f",
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        stop_cmd = f"{self.settings.prefix}{self.settings.stopCommand}"
        start_cmd = f"{self.settings.prefix}{self.settings.startCommand}"
        sleep_cmd = f"{self.settings.prefix}{self.settings.sleepCommand}"
        restart_cmd = f"{self.settings.prefix}{self.settings.restartCommand}"
        switchchannel_cmd = (
            f"{self.settings.prefix}{self.settings.switchChannelCommand}"
        )
        content = message.content.lower()
        if message.author.id in [self.bot.user.id] + self.settings.allowedUsers:
            if content.startswith(stop_cmd):
                await self.bot.log(
                    "stopping owo-dusk.. Please be warned that this sometimes doesn't work as expected. Please don't rely on it much.",
                    "#87875f",
                )
                self.bot.command_handler_status["sleep"] = True

            elif content.startswith(start_cmd):
                await self.bot.log("starting owo-dusk..", "#87875f")
                self.bot.command_handler_status["sleep"] = False

            elif content.startswith(sleep_cmd):
                after = content.split(sleep_cmd, 1)[1].strip()  # get text after command
                seconds = self.parse_seconds(after)

                if seconds is None:
                    seconds = (
                        self.settings.defaultSleepDuration
                    )  # fallback to default if no valid duration provided
                    await self.bot.log(
                        f"Invalid or no duration provided for sleep command. Defaulting to {seconds}s.",
                        "#87875f",
                    )

                if self.timed_task and not self.timed_task.done():
                    self.timed_task.cancel()  # cancel any existing timed task
                await self.bot.log(
                    f"Sleeping owo-dusk for {seconds} seconds..",
                    "#87875f",
                )
                self.bot.command_handler_status["sleep"] = True
                self.timed_task = asyncio.create_task(self.timed_reverse(seconds))

        if message.author.id == self.bot.user.id:
            if content.startswith(restart_cmd):
                await self.bot.log(
                    "Restarting owo-dusk after captcha..",
                    "#87875f",
                )
                self.bot.command_handler_status["captcha"] = False
            elif content.startswith(switchchannel_cmd):
                msg = content.removeprefix(switchchannel_cmd).strip()
                match = re.search(r"\d+", msg)
                if not match or " " in msg:
                    await self.bot.log(f"Invalid command used - {content}", "#87875f")
                    return

                try:
                    channel_id = int(match.group(0))
                    new_channel = await self.bot.fetch_channel(channel_id)
                    if new_channel:
                        await self.bot.empty_checks_and_switch(new_channel)
                        await self.handle_webhook(new_channel)

                except Exception as e:
                    await self.bot.log(
                        f"Failed to switch channel: {e} - Command: {content}", "#87875f"
                    )


async def setup(bot):
    await bot.add_cog(Chat(bot))
