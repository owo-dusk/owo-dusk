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


class OwoWatchdog:
    """
    Detects when OwO stops responding and pauses commands until it returns.

    The watchdog waits for a response to the last few messages. If none
    arrives, it sends a ping. If the ping gets no response, it enters standby
    and checks the OwO status API. A status of "ready" is confirmed with a
    ping before commands resume.
    """

    def __init__(
        self,
        send_ping,
        check_status,
        set_paused,
        log,
        unanswered_limit=3,
        response_timeout=10.0,
        status_poll_interval=60.0,
    ):
        self.send_ping = send_ping
        self.check_status = check_status
        self.set_paused = set_paused
        self.log = log
        self.unanswered_limit = unanswered_limit
        self.response_timeout = response_timeout
        self.status_poll_interval = status_poll_interval

        self.state = "idle"
        self._unanswered = 0
        self._response_seq = 0
        self._response_event = asyncio.Event()
        self._task = None

    @property
    def running(self):
        return self._task is not None

    def note_sent(self):
        """Record a sent command. Start the watchdog at the limit."""
        self._unanswered += 1
        if self._task is not None or self._unanswered < self.unanswered_limit:
            return

        self.state = "waiting"
        self.set_paused(True)
        self._task = asyncio.create_task(self._run(self._response_seq))

    def note_response(self):
        """Record a message from OwO. This also wakes a waiting watchdog."""
        self._unanswered = 0
        self._response_seq += 1
        self._response_event.set()

    async def join(self):
        """Wait for the current watchdog run to finish."""
        task = self._task
        if task is not None:
            await task

    async def cancel(self):
        """Stop the watchdog and clear the pause flag."""
        task = self._task
        self._task = None
        self.state = "idle"
        self._unanswered = 0
        if task is not None:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self.set_paused(False)

    async def _wait_for_response(self, start_seq, timeout):
        """Wait for an OwO message that arrived after start_seq."""
        self._response_event.clear()
        if self._response_seq != start_seq:
            return True
        try:
            await asyncio.wait_for(self._response_event.wait(), timeout)
            return True
        except asyncio.TimeoutError:
            return False

    async def _check_status(self):
        try:
            return await self.check_status()
        except Exception as e:
            await self.log(f"Failed to check the OwO status API: {e}", "#c25560")
            return False

    async def _send_ping(self):
        try:
            await self.send_ping()
        except Exception as e:
            await self.log(f"Failed to ping OwO: {e}", "#c25560")

    async def _run(self, start_seq):
        task = asyncio.current_task()
        try:
            if await self._wait_for_response(start_seq, self.response_timeout):
                await self.log("OwO responded, resuming commands", "#87af87")
                return

            await self.log("OwO did not respond, sending a ping", "#e6e65a")
            ping_seq = self._response_seq
            await self._send_ping()
            if await self._wait_for_response(ping_seq, self.response_timeout):
                await self.log("OwO answered the ping, resuming commands", "#87af87")
                return

            self.state = "standby"
            wait_seq = self._response_seq
            await self.log("OwO did not answer the ping, entering standby", "#c25560")
            first_check = True
            while True:
                if first_check:
                    first_check = False
                    if await self._check_status():
                        if await self._confirm_status_ready():
                            break
                    if self._response_seq != wait_seq:
                        break
                    continue

                if await self._wait_for_response(wait_seq, self.status_poll_interval):
                    break
                if await self._check_status():
                    if await self._confirm_status_ready():
                        break
                if self._response_seq != wait_seq:
                    break

            await self.log("OwO is back, resuming commands", "#87af87")
        except asyncio.CancelledError:
            raise
        except Exception as e:
            await self.log(f"OwO watchdog error: {e}", "#c25560")
        finally:
            if self._task is task:
                self.state = "idle"
                self._unanswered = 0
                self._task = None
                self.set_paused(False)

    async def _confirm_status_ready(self):
        await self.log(
            "The OwO status API reports ready, confirming with a ping",
            "#e6e65a",
        )
        confirm_seq = self._response_seq
        await self._send_ping()
        if await self._wait_for_response(confirm_seq, self.response_timeout):
            return True
        return False
