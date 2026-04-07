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
import aiosqlite


class databaseWorker:
    def __init__(self, db_path="utils/data/db.sqlite"):
        self.db_path = db_path
        self.queue = Queue()
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.start_loop, daemon=True)
        self.thread.start()

    def start_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.worker())

    def update_database(self, sql, params=None):
        self.queue.put((sql, params))

    async def get_from_db(self, sql, params=None):
        async with aiosqlite.connect(self.db_path, timeout=5) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(sql, params or ()) as cursor:
                return await cursor.fetchall()

    async def worker(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("PRAGMA synchronous=NORMAL;")
            await db.commit()

            while True:
                # Get queued SQL statements from thread-safe queue
                sql, params = await self.loop.run_in_executor(None, self.queue.get)
                # print(sql)
                try:
                    await db.execute(sql, params or ())
                    await db.commit()
                    # print("success!")
                except Exception as e:
                    print(f"Database Error: {e}")
                finally:
                    self.queue.task_done()
                    await asyncio.sleep(0.05)
