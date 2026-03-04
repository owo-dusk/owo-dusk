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
import random

from discord.ext import commands
from discord.ext.commands import ExtensionNotLoaded
#from uwu import MyClient


def cmd_argument(userid, ping):
    if userid:
        return f"<@{random.choice(userid)}>" if ping else random.choice(userid)
    else:
        return ""


class Pray(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pray_cmd_arguement = None
        self.curse_cmd_arguement = None
        self.startup = True
        # prevents pray/curse from being re-added if it is queued to be queued
        self.pray_curse_ongoing = False

        self.pray_cmd = {
            "cmd_name": "pray",
            "cmd_arguments": None,
            "prefix": True,
            "checks": True,
            "id": "pray",
        }

        self.curse_cmd = {
            "cmd_name": "curse",
            "cmd_arguments": None,
            "prefix": True,
            "checks": True,
            "id": "pray",  # using pray as id for curse to make it easier to close
        }
        self.cmd_names = []
        self.pray_channelId = 0
        self.curse_channelId = 0
        self.pray_channel = None
        self.curse_channel = None

    def fetch_setings(self, cmd):
        return getattr(self.bot.settings_dict_temp.commands, cmd)

    @property
    def cooldowns(self):
        return self.bot.settings_dict_temp.cooldowns

    async def safe_send_message(self, cmd, cmd_argument_data):
        while self.bot.command_handler_status["captcha"]:
            await asyncio.sleep(0.5)

        channel = self.__dict__[f"{cmd}_channel"]

        await channel.send(f"owo {cmd} {cmd_argument_data}")
        await self.bot.log(
            f"{cmd} send successfully in channel {channel.name}", "#4a3466"
        )

    async def start_pray_curse(self):
        self.pray_curse_ongoing = True
        cmds = [cmd for cmd in ["pray", "curse"] if self.fetch_setings(cmd).enabled]
        cmd = self.bot.random.choice(cmds)  # pick a random enabled cmd
        cnf = self.fetch_setings(cmd)
        if not self.startup:
            await self.bot.remove_queue(id="pray")
            await self.bot.sleep(cnf.get_cd())
            self.__dict__[f"{cmd}_cmd"]["checks"] = True
        else:
            await self.bot.sleep_till(self.cooldowns.shortCooldown)
            self.__dict__[f"{cmd}_cmd"]["checks"] = False

        cmd_argument_data = cmd_argument(cnf["userid"], cnf["pingUser"])

        self.__dict__[f"{cmd}_cmd"]["cmd_arguments"] = cmd_argument_data

        if cnf["customChannel"]["enabled"]:
            channelId = cnf["customChannel"]["channelId"]
            if (
                not self.__dict__[f"{cmd}_channel"]
                or self.__dict__[f"{cmd}_channelId"] != channelId
            ):
                try:
                    self.__dict__[f"{cmd}_channel"] = await self.bot.fetch_channel(
                        channelId
                    )
                    self.__dict__[f"{cmd}_channelId"] = channelId

                except Exception as e:
                    await self.bot.log(
                        f"Error - Failed to fetch channel with id {cnf['customChannel']['channelId']}: {e}",
                        "#c25560",
                    )
            await self.safe_send_message(cmd, cmd_argument_data)

        else:
            await self.bot.put_queue(self.__dict__[f"{cmd}_cmd"], priority=True)

        self.pray_curse_ongoing = False

        if cnf["customChannel"]["enabled"]:
            # It will be a pain to add retry logic for this as we handle this manually instead of relying on command handler.
            self.startup = False
            await self.start_pray_curse()
        elif self.startup:
            """
            Sometimes the pray/curse may have already ran twice within 5 mins after a successful run
            before owo-dusk is ran, this check is to fix it getting the code stuck.
            """
            await self.bot.sleep_till(self.cooldowns.shortCooldown)
            if self.startup:
                self.startup = False
                await self.start_pray_curse()

    async def cog_load(self):
        if (
            not self.fetch_setings("pray").enabled
            and not self.fetch_setings("curse").enabled
        ) or (self.cooldowns.reactionBot.prayAndCurse):
            try:
                asyncio.create_task(self.bot.unload_cog("cogs.pray"))
            except ExtensionNotLoaded:
                pass
        else:
            asyncio.create_task(self.start_pray_curse())

    async def cog_unload(self):
        await self.bot.remove_queue(id="pray")

    @commands.Cog.listener()
    async def on_message(self, message):
        if f"<@{self.bot.user.id}>" not in message.content:
            return

        if (
            message.channel.id == self.bot.cm.id
            and message.author.id == self.bot.owo_bot_id
        ):
            if (
                f"<@{self.bot.user.id}>** prays for **<@{self.fetch_setings('pray').user_id}>**!"
                in message.content
                or f"<@{self.bot.user.id}>** prays..." in message.content
                or f"<@{self.bot.user.id}>** puts a curse on **<@{self.fetch_setings('curse').user_id}>**!"
                in message.content
                or f"<@{self.bot.user.id}>** is now cursed." in message.content
                or "Slow down and try the command again" in message.content
            ):
                if not self.pray_curse_ongoing:
                    await self.bot.log("prayed/cursed successfully!", "#4a3466")
                    self.startup = False
                    await self.start_pray_curse()
                else:
                    await self.bot.log("ongoing pray/curse", "#4a3466")


async def setup(bot):
    await bot.add_cog(Pray(bot))
