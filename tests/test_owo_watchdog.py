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
import unittest

from core.owo_watchdog import OwoWatchdog


class OwoWatchdogTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.watchdog = None
        self.pings = 0
        self.answer_ping_at = None
        self.status_calls = 0
        self.status_results = []
        self.paused = []
        self.logs = []

    async def send_ping(self):
        self.pings += 1
        if self.pings == self.answer_ping_at and self.watchdog is not None:
            self.watchdog.note_response()

    async def check_status(self):
        self.status_calls += 1
        if self.status_results:
            return self.status_results.pop(0)
        return False

    def set_paused(self, paused):
        self.paused.append(paused)

    async def log(self, text, color):
        self.logs.append(text)

    def make_watchdog(self):
        self.watchdog = OwoWatchdog(
            send_ping=self.send_ping,
            check_status=self.check_status,
            set_paused=self.set_paused,
            log=self.log,
            response_timeout=0.05,
            status_poll_interval=0.05,
        )
        return self.watchdog

    async def wait_for_state(self, state, timeout=1.0):
        async def wait():
            while self.watchdog.state != state:
                await asyncio.sleep(0.001)

        await asyncio.wait_for(wait(), timeout)

    async def test_two_unanswered_messages_do_not_start_watchdog(self):
        watchdog = self.make_watchdog()

        watchdog.note_sent()
        watchdog.note_sent()

        self.assertFalse(watchdog.running)
        self.assertEqual(self.paused, [])

    async def test_response_before_timeout_resumes_without_ping(self):
        watchdog = self.make_watchdog()

        watchdog.note_sent()
        watchdog.note_sent()
        watchdog.note_sent()
        self.assertTrue(watchdog.running)

        watchdog.note_response()
        await watchdog.join()

        self.assertEqual(self.pings, 0)
        self.assertEqual(self.paused, [True, False])
        self.assertEqual(watchdog.state, "idle")

    async def test_ping_response_resumes_without_standby(self):
        watchdog = self.make_watchdog()
        self.answer_ping_at = 1

        watchdog.note_sent()
        watchdog.note_sent()
        watchdog.note_sent()
        await watchdog.join()

        self.assertEqual(self.pings, 1)
        self.assertEqual(self.paused, [True, False])
        self.assertEqual(watchdog.state, "idle")
        self.assertFalse(any("entering standby" in log for log in self.logs))

    async def test_standby_waits_for_status_ready_and_confirms_with_ping(self):
        watchdog = self.make_watchdog()
        self.status_results = [True]
        self.answer_ping_at = 2

        watchdog.note_sent()
        watchdog.note_sent()
        watchdog.note_sent()
        await watchdog.join()

        self.assertEqual(self.status_calls, 1)
        self.assertEqual(self.pings, 2)
        self.assertEqual(self.paused, [True, False])
        self.assertEqual(watchdog.state, "idle")

    async def test_response_during_standby_resumes(self):
        watchdog = self.make_watchdog()

        watchdog.note_sent()
        watchdog.note_sent()
        watchdog.note_sent()
        await self.wait_for_state("standby")
        watchdog.note_response()
        await watchdog.join()

        self.assertEqual(self.pings, 1)
        self.assertEqual(self.paused, [True, False])
        self.assertEqual(watchdog.state, "idle")

    async def test_cancel_clears_pause(self):
        watchdog = self.make_watchdog()

        watchdog.note_sent()
        watchdog.note_sent()
        watchdog.note_sent()
        await self.wait_for_state("waiting")
        await watchdog.cancel()

        self.assertEqual(self.paused, [True, False])
        self.assertEqual(watchdog.state, "idle")
        self.assertFalse(watchdog.running)


if __name__ == "__main__":
    unittest.main()
