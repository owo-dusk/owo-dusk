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

from collections import deque
from discord.ext import commands, tasks
from datetime import datetime, timezone, timedelta
# from uwu import MyClient


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.checks = []
        self.calc_time = timedelta(0)
        self.command_times = deque(maxlen=3)
        self.updated_between_cd = False

        self.last_msg = 0

    @property
    def command_hander_settings(self):
        return self.bot.settings_dict_temp.cooldowns.commandHandler

    def sleep_required(self):
        """makes sure three commands are within 5 second limit"""
        now = time.time()

        while self.command_times and now - self.command_times[0] >= 5:
            """Command has to be within 5 second limit"""
            self.command_times.popleft()

        if len(self.command_times) < 3:
            return False, 0
        else:
            wait_time = max(0, 5 - (now - self.command_times[0]))
            return True, wait_time

    async def sleep_between_commands(self, betweenCommands):
        if betweenCommands[0] > self.bot.cm_slowmode_cd:
            await self.bot.sleep_till(betweenCommands)
        else:
            await self.bot.sleep_till(self.bot.cm_slowmode_cd, cd_list=False)
            if not self.updated_between_cd:
                await self.bot.log(
                    f"Channel has a cooldown of {self.bot.cm_slowmode_cd}s, increasing delay between commands!",
                    "#8f6b09",
                )
                self.updated_between_cd = True

    async def start_commands(self):
        await self.bot.sleep_till(
            self.bot.global_settings_dict["account"]["commandsHandlerStartDelay"]
        )
        await self.bot.shuffle_queue()
        await self.bot.wait_until_ready()
        self.send_commands.start()
        self.monitor_checks.start()

    async def cog_load(self):
        """Run join_previous_giveaways when bot is ready"""
        asyncio.create_task(self.start_commands())

    """send commands"""

    @tasks.loop()
    async def send_commands(self):
        try:
            cnf = self.command_hander_settings
            priority, _, cmd = await self.bot.queue.get()
            cmd_id = cmd.get("id")
            custom_channel_id = cmd.get("channel")
            channel = None

            if custom_channel_id:
                try:
                    channel = await self.bot.fetch_channel(custom_channel_id)
                except Exception as e:
                    await self.bot.log(
                        f"Error - Failed to fetch channel with id {custom_channel_id}: {e}",
                        "#c25560",
                    )

            if priority != 0:
                while (
                    time.time() - self.bot.cmds_state["global"]["last_ran"]
                ) < cnf.betweenCommands[0]:
                    await self.sleep_between_commands(cnf.betweenCommands)

            sleep_req, sleep_time = self.sleep_required()
            if sleep_req:
                await self.bot.log(
                    f"sleep required by {sleep_time}s (to prevent `slow down` message)",
                    "#8f6b09",
                )
                await self.bot.sleep_till([sleep_time, sleep_time + 0.4])
                self.command_times.clear()

            """Update Command state"""
            await self.bot.upd_cmd_state(cmd_id)

            """Append to checks"""
            if cmd.get("checks") and cmd_id:
                in_queue = await self.bot.search_checks(id=cmd_id)
                if not in_queue:
                    async with self.bot.lock:
                        self.bot.checks.append(cmd)

            if self.bot.settings_dict_temp.useSlashCommands and cmd.get(
                "slash_cmd_name", False
            ):
                await self.bot.slashCommandSender(
                    cmd["slash_cmd_name"],
                    self.bot.misc["command_info"][cmd_id]["log_color"],
                    channel=channel,
                )
            else:
                await self.bot.send(
                    self.bot.construct_command(
                        cmd, guild_id=channel.guild.id if channel else None
                    ),
                    self.bot.misc["command_info"][cmd_id]["log_color"],
                    channel=channel,
                )

            """add command to the deque"""
            self.command_times.append(time.time())

        except Exception as e:
            await self.bot.log(
                f"Error - send_commands() loop: {e}. {cmd.get('cmd_name', None)}",
                "#c25560",
            )
            await self.sleep_between_commands(cnf.betweenCommands)

    @tasks.loop(seconds=1)
    async def monitor_checks(self):
        try:
            delay = self.command_hander_settings.readdingToQueue
            current_time = datetime.now(timezone.utc)
            if (
                not self.bot.command_handler_status["state"]
                or self.bot.command_handler_status["sleep"]
                or self.bot.command_handler_status["captcha"]
                or self.bot.command_handler_status["hold_handler"]
            ):
                self.calc_time += current_time - getattr(
                    self, "last_check_time", current_time
                )
            else:
                for command in self.bot.checks[:]:
                    cnf = self.bot.cmds_state[command["id"]]
                    if (time.time() - cnf["last_ran"] > delay) and not cnf["in_queue"]:
                        async with self.bot.lock:
                            self.bot.checks.remove(command)
                        await self.bot.put_queue(command)

                self.calc_time = timedelta(0)
            self.last_check_time = current_time
        except Exception as e:
            await self.bot.log(f"Error - monitor_checks(): {e}", "#c25560")

    """@commands.Cog.listener()
    async def on_message(self, message):
        self.last_msg = time.time()"""


async def setup(bot):
    await bot.add_cog(Commands(bot))
