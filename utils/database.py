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

import os
import sqlite3

from utils.constants import database_version
from utils.errors import suppress_and_log
from utils.loader import misc_dict
from utils.system.system import compare_versions, console


@suppress_and_log("Database Initialisation")
def create_database(db_path="utils/data/db.sqlite"):
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        try:
            c.execute("SELECT value FROM meta_data WHERE key = 'version'")
            row = c.fetchone()
            current_version = row[0] if row else None
        except sqlite3.OperationalError:
            # Table meta_data doesn't exist yet
            current_version = None
        finally:
            conn.close()

        # 2. If version is wrong or missing, delete the file
        if current_version and compare_versions(current_version, database_version):
            console.print(
                f"Version mismatch (Found: {current_version}, Expected: {database_version}). Recreating DB...",
                style="orange_red1",
            )
            os.remove(db_path)

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute(
        "CREATE TABLE IF NOT EXISTS commands (name TEXT PRIMARY KEY, count INTEGER)"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS cowoncy_earnings (user_id TEXT, hour INTEGER, earnings INTEGER, PRIMARY KEY (user_id, hour))"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS gamble_winrate (hour INTEGER PRIMARY KEY, wins INTEGER, losses INTEGER, net INTEGER)"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS user_stats (user_id TEXT PRIMARY KEY, daily REAL, lottery REAL, cookie REAL, giveaways REAL, captchas INTEGER, cowoncy INTEGER, boss REAL, boss_ticket INTEGER)"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS meta_data (key TEXT PRIMARY KEY, value INTEGER)"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS command_priority (user_id TEXT, command_name TEXT, priority INTEGER, PRIMARY KEY (user_id, command_name))"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS pupiku (user_id TEXT, cmd TEXT, times_to_run INTEGER, last_ran REAL, PRIMARY KEY (user_id, cmd))"
    )
    # Switch to WAL mode.
    c.execute("PRAGMA journal_mode=WAL;")

    # Populate
    # -- gamble_winrate
    for hr in range(24):
        # hour does not have 24 in 24 hr format!!
        c.execute(
            "INSERT OR IGNORE INTO gamble_winrate (hour, wins, losses, net) VALUES (?, ?, ?, ?)",
            (hr, 0, 0, 0),
        )

    # -- meta data
    c.execute(
        "INSERT OR IGNORE INTO meta_data (key, value) VALUES (?, ?)",
        ("gamble_winrate_last_checked", 0),
    )
    c.execute(
        "INSERT OR IGNORE INTO meta_data (key, value) VALUES (?, ?)",
        ("cowoncy_earnings_last_checked", 0),
    )

    # `INSERT OR UPDATE` is not used since we will be comparing old value (if any) ------ (check!!)
    c.execute(
        "INSERT OR IGNORE INTO meta_data (key, value) VALUES (?, ?)",
        ("version", database_version),
    )

    c.execute(
        "INSERT OR IGNORE INTO meta_data (key, value) VALUES (?, ?)",
        ("event_till_timestamp", 0),
    )

    # -- command priority
    c.execute("SELECT * FROM command_priority WHERE user_id = ?", ("default",))
    rows = c.fetchall()
    populate = False
    if not rows:
        populate = True

    if not populate:
        # 0 -> user_id
        # 1 -> command_name
        # 2 -> priority
        temp_list = [(row[1], int(row[2])) for row in rows]
        for key, value in misc_dict["command_info"].items():
            if (key, value["priority"]) not in temp_list:
                c.execute("DELETE FROM command_priority")
                populate = True
                break

    if populate:
        for key, value in misc_dict["command_info"].items():
            # We will be putting a `DEFAULT` value here to make it easier to compare to misc.json.
            # This is to ensure we do update in two cases:
            # 1) when priority is changed
            # 3) when a new item is added to priority
            c.execute(
                "INSERT OR IGNORE INTO command_priority (user_id, command_name, priority) VALUES (?, ?, ?)",
                ("default", key, value.get("priority")),
            )

    # -- commands
    for cmd in misc_dict["command_info"].keys():
        c.execute(
            "INSERT OR IGNORE INTO commands (name, count) VALUES (?, ?)", (cmd, 0)
        )

    # -- end --#
    conn.commit()
    conn.close()
