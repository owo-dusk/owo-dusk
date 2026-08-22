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
import itertools
import time
from contextlib import asynccontextmanager
from copy import deepcopy

from utils.errors import suppress_and_log


class CommandHandlerStatus:
    def __init__(self):
        # This is
        self.state = True
        # This is toggled when a captcha appears
        self.captcha = False
        # This is toggled when sleep is required (user preference)
        self.sleep = False
        # This is toggled for temporary pauses as required by other commands
        self.hold_handler = False


class CommandHandler:
    def __init__(self, client):
        self.lock = None
        # Queue at which commands will be queued
        self.queue = asyncio.PriorityQueue()
        # Tie-breaker
        self.cmd_counter = itertools.count()
        # Priorities of command. Will be populated from `database` from `misc.json` config
        self.cmd_priorities = {}
        # A list of commands that must be re-ran
        self.checks = []
        # State event for setting `self.state`
        self.state_event = asyncio.Event()

        self.client = client

        self.cmds_state = {"global": {"last_ran": 0}}
        for key in self.client.misc["command_info"]:
            self.cmds_state[key] = {
                "in_queue": False,
                "in_monitor": False,
                "last_ran": 0,
            }

        self.command_handler_status = CommandHandlerStatus()

    @asynccontextmanager
    async def _hold_or_create_lock(self):
        if not self.lock:
            self.lock = asyncio.Lock()

        async with self.lock:
            yield

    @property
    def should_not_send(self):
        """
        Commands must not be send in these cases
        """
        return (
            not self.command_handler_status.state
            or self.command_handler_status.hold_handler
            or self.command_handler_status.sleep
            or self.command_handler_status.captcha
        )

    @property
    def can_send_if_priority(self):
        """
        Some commands are required to be send quickly. So if its just
        """
        return (
            not self.command_handler_status.sleep
            and not self.command_handler_status.hold_handler
            and not self.command_handler_status.captcha
        )

    @suppress_and_log("Attempting to append queue")
    async def put_queue(self, cmd_data, priority=False, quick=False):
        while self.should_not_send:
            if priority and self.can_send_if_priority:
                break
            await asyncio.sleep(self.client.random.uniform(1.4, 2.9))

        if self.cmds_state[cmd_data["id"]]["in_queue"]:
            # Add exception for custom commands
            if cmd_data["id"] != "customcommand":
                # Ensure command already in queue is not readded to prevent spam
                await self.client.log(
                    f"Error - command with id: {cmd_data['id']} already in queue, being attempted to be added back.",
                    "#c25560",
                )
                return

        # Get priority
        priority_int = self.cmd_priorities.get(cmd_data["id"]) if not quick else 0

        if not priority_int and priority_int != 0:
            await self.client.log(
                f"Error - command with id: {cmd_data['id']} is missing priority.",
                "#c25560",
            )
            return

        async with self._hold_or_create_lock():
            await self.queue.put(
                (
                    priority_int,  # Priority to sort commands with
                    next(self.cmd_counter),  # A counter to serve as a tie-breaker
                    deepcopy(cmd_data),  # actual data
                )
            )
            self.cmds_state[cmd_data["id"]]["in_queue"] = True

    @suppress_and_log("Remove Queue")
    async def remove_queue(self, cmd_data=None, id=None):
        if not cmd_data and not id:
            await self.client.log(
                "Error: No id or command data provided for removing item from queue.",
                "#c25560",
            )
            return

        async with self._hold_or_create_lock():
            for index, command in enumerate(self.checks):
                if cmd_data:
                    if command == cmd_data:
                        self.checks.pop(index)
                else:
                    if command.get("id", None) == id:
                        self.checks.pop(index)

    async def search_checks(self, id):
        async with self._hold_or_create_lock():
            for command in self.checks:
                if command.get("id", None) == id:
                    return True
            return False

    async def shuffle_queue(self):
        async with self._hold_or_create_lock():
            items = []
            while not self.queue.empty():
                items.append(await self.queue.get())

            self.client.random.shuffle(items)

            for item in items:
                await self.queue.put(item)

    async def upd_cmd_state(self, id, reactionBot=False):
        async with self._hold_or_create_lock():
            self.cmds_state["global"]["last_ran"] = time.time()
            self.cmds_state[id]["last_ran"] = time.time()
            if not reactionBot:
                self.cmds_state[id]["in_queue"] = False
            self.client.db.update_cmd_db(id)

    async def set_stat(self, value):
        if value:
            self.command_handler_status.state = True
            self.state_event.set()
        else:
            while not self.command_handler_status.state:
                await self.state_event.wait()
            self.command_handler_status.state = False
            self.state_event.clear()
