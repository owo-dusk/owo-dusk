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
from concurrent.futures import Future
from queue import Empty, Queue

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

    def update_database(self, sql, params=None, wait=False):
        future = Future() if wait else None
        self.queue.put((sql, params, future))
        return future

    async def update_database_async(self, sql, params=None):
        """
        A future is passed and awaited until its done.
        """
        future = self.update_database(sql, params, wait=True)
        return await asyncio.wrap_future(future)

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
                sql, params, fut = await self.loop.run_in_executor(None, self.queue.get)
                batch = [(sql, params, fut)]

                while len(batch) < 200:
                    try:
                        batch.append(self.queue.get_nowait())
                    except Empty:
                        break

                succeeded = []
                try:
                    for s, p, f in batch:
                        try:
                            await db.execute(s, p or ())
                            succeeded.append(f)
                        except Exception as e:
                            print(f"Database Error (statement): {e}")
                            if f is not None:
                                f.set_exception(e)

                    # Only commit once, this way it doesn't take up much cpu while avoiding unnecessary restrictions.
                    await db.commit()

                    for f in succeeded:
                        """
                        `f` here is the future. When await is required, Future is passed alongside the queue. Once done
                        """
                        if f is not None:
                            f.set_result(True)
                except Exception as e:
                    print(f"Database Error (commit): {e}")
                    for f in succeeded:
                        if f is not None:
                            f.set_exception(e)
                finally:
                    for _ in batch:
                        self.queue.task_done()
