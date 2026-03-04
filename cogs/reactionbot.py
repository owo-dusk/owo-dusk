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

from discord.ext import commands, tasks
from discord.ext.commands import ExtensionNotLoaded
#from uwu import MyClient


class Reactionbot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cmd_states = {"hunt": 0, "battle": 0, "owo": 0, "pray": 0}

    @property
    def settings(self):
        return self.bot.settings_dict_temp.commands

    @property
    def reaction_bot_settings(self):
        return self.bot.settings_dict_temp.cooldowns.reactionBot

    def fetch_setings(self, cmd):
        return getattr(self.bot.settings_dict_temp.commands, cmd)

    def fetch_cmd(self, id):
        hunt_shortform = self.settings.hunt.shortform
        battle_shortform = self.settings.battle.shortform

        cmd_name = {
            "hunt": self.bot.alias["hunt"][
                "normal" if not hunt_shortform else "shortform"
            ],
            "battle": self.bot.alias["battle"][
                "normal" if not battle_shortform else "shortform"
            ],
            "owo": self.bot.alias["owo"]["normal"],
        }

        arg = ""
        if id in {"pray", "curse"} and self.fetch_setings(id).user_id:
            user_id = self.bot.random.choice(self.fetch_setings(id).user_id)
            if self.fetch_setings(id).ping_user:
                arg = f"<@{user_id}>"
            else:
                arg = str(user_id)

        base = {
            "cmd_name": cmd_name.get(id, id),
            "prefix": id != "owo",
            "checks": False,
            "cmd_arguments": arg,
            "slash_cmd_name": id if id in {"hunt", "battle"} else None,
            "id": id if id != "curse" else "pray",
        }

        return base

    def check_cmd_state(self, cmd, return_dict=False):
        enabled_dict = {
            "hunt": self.settings.hunt.enabled
            and self.reaction_bot_settings.huntAndBattle,
            "battle": self.settings.battle.enabled
            and self.reaction_bot_settings.huntAndBattle,
            "owo": self.reaction_bot_settings.owo and self.settings.owo.enabled,
            "pray": self.settings.pray.enabled
            and self.reaction_bot_settings.prayAndCurse,
            "curse": self.settings.curse.enabled
            and self.reaction_bot_settings.prayAndCurse,
        }

        return enabled_dict.get(cmd) if not return_dict else enabled_dict

    def cmd_retry_required(self, cmd):
        cmd_id = cmd if cmd != "curse" else "pray"
        priority_dict = self.bot.misc["command_info"]
        last_time = self.cmd_states[cmd_id]
        # The 5s here is incase of delays.
        return (time.time() - last_time) > priority_dict[cmd_id]["basecd"] + 5

    @tasks.loop(seconds=5)
    async def check_stuck_state(self):
        enabled_dict = self.check_cmd_state(cmd=None, return_dict=True)
        for cmd, state in enabled_dict.items():
            if state and self.cmd_retry_required(cmd):
                await self.send_cmd(cmd)

    async def send_cmd(self, cmd):
        await self.bot.sleep(self.reaction_bot_settings.get_cd())
        await self.bot.put_queue(self.fetch_cmd(cmd), quick=True, priority=True)
        self.cmd_states[cmd if cmd != "curse" else "pray"] = time.time()

    async def startup_handler(self):
        await self.bot.set_stat(False)
        """Define alias of commands"""
        hunt = self.check_cmd_state("hunt")
        battle = self.check_cmd_state("battle")
        pray = self.check_cmd_state("pray")
        curse = self.check_cmd_state("curse")

        """Hunt/Battle"""
        if hunt and battle:
            print("starting hunt and battle!")
            await self.send_cmd("hunt")
            await self.send_cmd("battle")
        elif hunt or battle:
            await self.send_cmd("hunt" if hunt else "battle")

        """OwO/UwU"""
        if self.check_cmd_state("owo"):
            await self.send_cmd("owo")

        """Pray/Curse"""
        if pray or curse:
            cmds = []
            if pray:
                cmds.append("pray")
            if curse:
                cmds.append("curse")
            await self.send_cmd(self.bot.random.choice(cmds))
        await self.bot.set_stat(True)
        """Start stuck state checker"""
        self.check_stuck_state.start()

    """gets executed when the cog is first loaded"""

    async def cog_load(self):
        hunt = self.check_cmd_state("hunt")
        battle = self.check_cmd_state("battle")
        pray = self.check_cmd_state("pray")
        curse = self.check_cmd_state("curse")
        owo = self.check_cmd_state("owo")

        if not (hunt or battle or pray or curse or owo):
            try:
                asyncio.create_task(self.bot.unload_cog("cogs.reactionbot"))
            except ExtensionNotLoaded:
                pass
        else:
            asyncio.create_task(self.startup_handler())

    @commands.Cog.listener()
    async def on_message(self, message):
        hunt = self.check_cmd_state("hunt")
        battle = self.check_cmd_state("battle")
        pray = self.check_cmd_state("pray")
        curse = self.check_cmd_state("curse")
        owo = self.check_cmd_state("owo")

        if (
            message.channel.id == self.bot.cm.id
            and message.author.id == self.bot.reaction_bot_id
        ):
            if (
                f"<@{self.bot.user.id}>" in message.content
                or self.bot.user.name in message.content
            ):
                if "**OwO**" in message.content and owo:
                    await self.send_cmd("owo")

                elif "**hunt/battle**" in message.content and (hunt or battle):
                    if hunt and battle:
                        await self.send_cmd("hunt")
                        await self.send_cmd("battle")
                    else:
                        cmd = "hunt" if hunt else "battle"
                        await self.send_cmd(cmd)

                elif "**pray/curse**" in message.content and (pray or curse):
                    cmds = []
                    if pray:
                        cmds.append("pray")
                    if curse:
                        cmds.append("curse")
                    await self.send_cmd(self.bot.random.choice(cmds))


async def setup(bot):
    await bot.add_cog(Reactionbot(bot))
