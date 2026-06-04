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
import heapq
import string
import time
import random
import itertools

from discord.ext import tasks
from discord.ext.commands import ExtensionNotLoaded
from cogs._BASE import BaseCog

"""
These commands: owo, pray, curse, level - can simply be send at specific intervals
"""

"""
TASK:

handle pray/curse enabled at same times

"""

LOOPABLE_COMMANDS = ["owo", "pray", "curse", "level"]


def generate_random_string(min, max):
    """something like a list?"""
    characters = string.ascii_lowercase + " "
    length = random.randint(min, max)
    random_string = "".join(random.choice(characters) for _ in range(length))
    return random_string


async def fetch_quotes(session):
    quotes_url = "https://favqs.com/api/qotd"
    async with session.get(quotes_url) as response:
        if response.status == 200:
            data = await response.json()
            # quote = data["quote"]["body"]
            if data.get("quote"):
                return data["quote"].get("body", None)


def pray_cmd_argument(userid, ping):
    if userid:
        return f"<@{random.choice(userid)}>" if ping else random.choice(userid)
    else:
        return ""


class Looper(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.startup = True
        self.counter = itertools.count()  # for tie-breaking
        self.schedule_heap = []  # heap we are going to use

        # For making code easier to read, last_ran will be connected
        # to `heap_settings` property
        self.last_ran = {"owo": 0, "pray": 0, "curse": 0, "level": 0}

    @property
    def owo_settings(self):
        return self.bot.settings_dict_temp.commands.owo

    @property
    def pray_settings(self):
        return self.bot.settings_dict_temp.commands.pray

    @property
    def curse_settings(self):
        return self.bot.settings_dict_temp.commands.curse

    @property
    def reaction_bot_settings(self):
        return self.bot.settings_dict_temp.cooldowns.reactionBot

    @property
    def is_enabled_dict(self):
        pray_curse_reaction = self.reaction_bot_settings.prayAndCurse
        return {
            "owo": self.owo_settings.enabled and not self.reaction_bot_settings.owo,
            "level": self.level_settings.enabled,
            "pray": self.pray_settings.enabled and not pray_curse_reaction,
            "curse": self.curse_settings.enabled and not pray_curse_reaction,
        }

    def get_pray_curse_settings(self, cmd):
        # temporary, look if something like to_dict exists for objects
        if cmd == "pray":
            return self.pray_settings
        else:  # Please don't accidently misspell lol
            return self.curse_settings

    @property
    def level_settings(self):
        return self.bot.settings_dict_temp.commands.lvlGrind

    def heap_settings(self, cmd):
        now = time.monotonic()
        enabled = self.is_enabled_dict
        return {
            "owo": {
                "enabled": enabled["owo"],
                "next_run": now + self.owo_settings.get_cd(),
                "send": self.send_owo,
                "id": "owo",
            },
            "level": {
                "enabled": enabled["level"],
                "next_run": now + self.level_settings.get_cd(),
                "send": self.send_level,
                "id": "level",
            },
            # This is soo cool, wrapping function in another function (lambda)
            # also owo's cd being used here is intentional but temporary btw
            # i mean it just does what its supposed to do: send command first!
            "pray": {
                "enabled": enabled["pray"],
                "next_run": now + (self.pray_settings.get_cd() if not self.startup else self.owo_settings.get_cd()),
                "send": lambda: self.send_pray_curse("pray"),
                "id": "pray",
            },
            "curse": {
                "enabled": enabled["curse"],
                "next_run": now + (self.curse_settings.get_cd() if not self.startup else self.owo_settings.get_cd()),
                "send": lambda: self.send_pray_curse("curse"),
                "id": "curse",
            },
        }[cmd]

    def append_heap(self, cmd_name):
        settings = self.heap_settings(cmd_name)
        if settings["enabled"]:
            heapq.heappush(
                self.schedule_heap, (settings["next_run"], next(self.counter), settings)
            )

    def try_append_all(self):
        # sometimes I love how references work in Python
        # sometimes I hate them.... ;<
        ids = LOOPABLE_COMMANDS.copy()
        for _, _, settings in self.schedule_heap:
            if settings["id"] in ids:
                ids.remove(settings["id"])
        for cmd in ids:
            self.append_heap(cmd)

    def check(self, message, content, channel_id=None):
        return (
            message.author.id == self.bot.user.id
            and message.channel.id == (channel_id if channel_id else self.bot.cm.id)
            and message.content == content
        )

    async def block_till_send(self, content, channel_id=None):
        try:
            await self.bot.wait_for(
                "message", check=lambda m: self.check(m, content, channel_id), timeout=30.0
            )
            print(f"recieved msg for {content}")
        except asyncio.TimeoutError:
            print("this is bad, check failed miserably!")

    async def send_owo(self):
        cmd = {
            "cmd_name": self.bot.alias["owo"]["normal"],
            "prefix": False,
            "checks": False,
            "id": "owo",
        }

        # We are using quick for OwO for faster leaderboard progression and accuracy
        await self.bot.put_queue(cmd, quick=self.owo_settings.prioritise)
        await self.block_till_send(cmd["cmd_name"])

    async def send_pray_curse(self, cmd_name):
        cnf = self.get_pray_curse_settings(cmd_name)
        cmd = {
            "cmd_name": cmd_name,
            "cmd_arguments": pray_cmd_argument(cnf.user_id, cnf.ping_user),
            "prefix": True,
            "checks": False,
            "id": "pray",  # pray will be utilised as id for curse aswell
            "channel": None
            if not cnf.custom_channel.enabled
            else cnf.custom_channel.channel,
        }

        await self.bot.put_queue(cmd)
        self.startup = False
        await self.block_till_send(self.bot.settings_dict_temp.prefix + cmd["cmd_name"])

    async def send_level(self):
        if self.level_settings.useQuote:
            msg = await fetch_quotes(self.bot.session)
        else:
            msg = generate_random_string(
                self.level_settings.minLength, self.level_settings.maxLength
            )
        cmd = {
            "cmd_name": msg,
            "prefix": False,
            "checks": False,
            "id": "level",
        }

        await self.bot.put_queue(cmd)
        await self.block_till_send(cmd["cmd_name"])

    @tasks.loop()
    async def initiate_loop(self):
        self.try_append_all()

        if not self.schedule_heap:
            # weird why the code wouldnt stop
            await asyncio.sleep(1)
            return

        next_run, _, settings = self.schedule_heap[0]
        sleep_for = next_run - time.monotonic()
        if sleep_for > 0:
            # Guard against incase a command already finished its wait time
            # Iam curious how .sleep handles negatives 0o
            await asyncio.sleep(sleep_for)
        heapq.heappop(self.schedule_heap)
        print(f"sending {settings['id']}")
        await settings["send"]()
        self.append_heap(settings["id"])
        print(self.schedule_heap)

    """gets executed when the cog is first loaded"""

    async def cog_load(self):
        should_run = False
        for item in LOOPABLE_COMMANDS:
            if self.is_enabled_dict[item]:
                should_run = True

        if not should_run:
            try:
                asyncio.create_task(self.bot.unload_cog("cogs.looper"))
            except ExtensionNotLoaded:
                pass
        else:
            self.initiate_loop.start()

    async def cog_unload(self):
        # if not self.initiate_loop.done():
        self.initiate_loop.cancel()


async def setup(bot):
    await bot.add_cog(Looper(bot))
