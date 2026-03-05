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
import threading
from queue import Queue
import aiohttp


class webhookSender:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
        self.queue = Queue()
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.start_loop, daemon=True)
        self.thread.start()

    def start_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.worker())

    def send(self, data):
        # Put data to the queue, passed from webhookHandler() function.
        self.queue.put(data)

    async def custom_send(self, data, webhook):
        # Task: create queue for this as well in case
        # Task 2: Reuse session
        async with aiohttp.ClientSession() as session:
            async with session.post(
                webhook,
                json=data,
                headers={"Content-Type": "application/json"},
            ) as resp:
                _ = await resp.text()
                # Task 3: handle webhook ratelimits

    async def worker(self):
        async with aiohttp.ClientSession() as session:
            while True:
                # Creates new thread for queue.get
                data = await self.loop.run_in_executor(None, self.queue.get)
                try:
                    async with session.post(
                        self.webhook_url,
                        json=data,  # payload
                        headers={"Content-Type": "application/json"},
                    ) as _:
                        # text = await resp.text()
                        # print(f"[Webhook] {resp.status}: {text}")
                        pass
                finally:
                    self.queue.task_done()
                    await asyncio.sleep(0.1)
