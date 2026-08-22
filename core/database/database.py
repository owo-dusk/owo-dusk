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

from functools import wraps

import utils.timestamp as utils

from . import worker

# Thankfully Database class won't be touching this, would have been a mess otherwise!
database_handler = worker.databaseWorker()


def log_stats_if_required(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self.client.global_settings_dict.database.logStatistics:
            return func(self, *args, **kwargs)

    return wrapper


class Database:
    def __init__(self, client):
        # We pass a "reference" here
        self.client = client

    async def update_priorities(self):
        # Check if already in db
        res = await database_handler.get_from_db(
            "SELECT * FROM command_priority WHERE user_id = ?",
            (str(self.client.user.id),),
        )
        if res:
            for row in res:
                # 0 -> user_id
                # 1 -> command_name
                # 2 -> priority
                self.client.ch.cmd_priorities[row[1]] = int(row[2])
        else:
            # Group items using tiers
            tiers_map = {}
            for key, value in self.client.misc["command_info"].items():
                tiers_map[value["priority"]] = tiers_map.get(value["priority"], []) + [
                    key
                ]

            # randomising based on these tiers
            base_priority = 0
            for tier in sorted(tiers_map):
                temp_list = tiers_map[tier]
                self.client.random.shuffle(temp_list)
                for item in temp_list:
                    # This way base_priority will remain above 0, ensuring it doesn't hit quick send.
                    base_priority += 1
                    self.client.ch.cmd_priorities[item] = base_priority
                    await database_handler.update_database_async(
                        """INSERT OR REPLACE INTO command_priority (user_id, command_name, priority)
                        VALUES (?, ?, ?)""",
                        (str(self.client.user.id), item, base_priority),
                    )

        # print(self.client.user.name, "->", self.client.ch.cmd_priorities)

    def update_cash_db(self):
        hr = utils.get_hour()

        database_handler.update_database(
            """UPDATE cowoncy_earnings
            SET earnings = ?
            WHERE user_id = ? AND hour = ?""",
            (self.client.user_status["net_earnings"], self.client.user.id, hr),
        )

        database_handler.update_database(
            "UPDATE user_stats SET cowoncy = ? WHERE user_id = ?",
            (self.client.user_status["balance"], self.client.user.id),
        )

    @log_stats_if_required
    def update_captcha_db(self):
        database_handler.update_database(
            "UPDATE user_stats SET captchas = captchas + 1 WHERE user_id = ?",
            (self.client.user.id,),
        )

    def update_giveaway_db(self, last_ran):
        database_handler.update_database(
            "UPDATE user_stats SET giveaways = ? WHERE user_id = ?",
            (last_ran, self.client.user.id),
        )

    async def fetch_giveaway_db(self):
        results = await database_handler.get_from_db(
            "SELECT giveaways FROM user_stats WHERE user_id = ?", (self.client.user.id,)
        )
        if results:
            return results[0]["giveaways"]
        return None

    async def populate_stats_db(self):
        await database_handler.update_database_async(
            "INSERT OR IGNORE INTO user_stats (user_id, daily, lottery, cookie, giveaways, captchas, cowoncy, boss, boss_ticket, pup, piku, army) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (self.client.user.id, 0, 0, 0, 0, 0, 0, 0, 3, 0, 0, 0),
        )

    def update_stats_db(self, column_name, value):
        if column_name not in {
            "daily",
            "lottery",
            "cookie",
            "giveaways",
            "boss",
            "pup",
            "piku",
            "army",
        }:
            # Captcha and cowoncy handled separately
            raise ValueError("Invalid column name.")

        database_handler.update_database(
            f"UPDATE user_stats SET {column_name} = ? WHERE user_id = ?",
            (value, self.client.user.id),
        )

    def consume_boss_ticket(self, revert=False):
        if not revert:
            database_handler.update_database(
                "UPDATE user_stats SET boss_ticket = boss_ticket - 1 WHERE user_id = ? and boss_ticket > 0",
                (self.client.user.id,),
            )
        else:
            database_handler.update_database(
                "UPDATE user_stats SET boss_ticket = boss_ticket + 1 WHERE user_id = ? and boss_ticket < 3",
                (self.client.user.id,),
            )

    async def fetch_boss_stats(self):
        results = await database_handler.get_from_db(
            "SELECT boss, boss_ticket FROM user_stats WHERE user_id = ?",
            (self.client.user.id,),
        )
        if results:
            return results[0]["boss"], results[0]["boss_ticket"]
        print(
            f"seems like user_stats have not been properly initialised -> {self.client.user.name}"
        )
        return 0, 3

    def reset_boss_ticket(self, empty=False):
        if not empty:
            # We have a total of 3 tickets per day.
            database_handler.update_database(
                "UPDATE user_stats SET boss_ticket = ? WHERE user_id = ?",
                (3, self.client.user.id),
            )
        else:
            database_handler.update_database(
                "UPDATE user_stats SET boss_ticket = ? WHERE user_id = ?",
                (0, self.client.user.id),
            )

    async def populate_cowoncy_earnings(self, update=False):
        today_str = utils.get_date()

        for i in range(24):
            if not update:
                await database_handler.update_database_async(
                    "INSERT OR IGNORE INTO cowoncy_earnings (user_id, hour, earnings) VALUES (?, ?, ?)",
                    (self.client.user.id, i, 0),
                )

        rows = await database_handler.get_from_db(
            "SELECT value FROM meta_data WHERE key = ?",
            ("cowoncy_earnings_last_checked",),
        )

        last_reset_str = rows[0]["value"] if rows else "0"

        if last_reset_str == today_str:
            # Handle gap between cowoncy chart
            cur_hr = utils.get_hour()
            last_cash = 0
            for hr in range(cur_hr + 1):
                hr_row = await database_handler.get_from_db(
                    "SELECT earnings FROM cowoncy_earnings WHERE user_id = ? AND hour = ?",
                    (self.client.user.id, hr),
                )
                # Note: negative values are allowed.
                if hr_row and hr_row[0]["earnings"] != 0:
                    last_cash = hr_row[0]["earnings"]
                elif last_cash != 0:
                    await database_handler.update_database_async(
                        "UPDATE cowoncy_earnings SET earnings = ? WHERE hour = ? AND user_id = ?",
                        (last_cash, hr, self.client.user.id),
                    )
            # Return once done as we don't want reset.
            return

        for i in range(24):
            await database_handler.update_database_async(
                "UPDATE cowoncy_earnings SET earnings = 0 WHERE user_id = ? AND hour = ?",
                (self.client.user.id, i),
            )

        await database_handler.update_database_async(
            "UPDATE meta_data SET value = ? WHERE key = ?",
            (today_str, "cowoncy_earnings_last_checked"),
        )

    async def fetch_net_earnings(self):
        self.client.user_status["net_earnings"] = 0
        rows = await database_handler.get_from_db(
            "SELECT earnings FROM cowoncy_earnings WHERE user_id = ? ORDER BY hour",
            (self.client.user.id,),
        )

        cowoncy_list = [row["earnings"] for row in rows]

        for item in reversed(cowoncy_list):
            if item != 0:
                self.client.user_status["net_earnings"] = item
                break

    async def reset_gamble_wins_or_losses(self):
        today_str = utils.get_date()

        rows = await database_handler.get_from_db(
            "SELECT value FROM meta_data WHERE key = ?",
            ("gamble_winrate_last_checked",),
        )

        last_reset_str = rows[0]["value"] if rows else "0"

        if last_reset_str == today_str:
            return

        for hour in range(24):
            database_handler.update_database(
                "UPDATE gamble_winrate SET wins = 0, losses = 0, net = 0 WHERE hour = ?",
                (hour,),
            )

        database_handler.update_database(
            "UPDATE meta_data SET value = ? WHERE key = ?",
            (today_str, "gamble_winrate_last_checked"),
        )

    @log_stats_if_required
    def update_cmd_db(self, cmd):
        database_handler.update_database(
            "UPDATE commands SET count = count + 1 WHERE name = ?", (cmd,)
        )

    @log_stats_if_required
    def update_gamble_db(self, item="wins"):
        hr = utils.get_hour()

        if item not in {"wins", "losses"}:
            raise ValueError("Invalid column name.")

        database_handler.update_database(
            f"UPDATE gamble_winrate SET {item} = {item} + 1 WHERE hour = ?", (hr,)
        )

    async def fetch_cmd_lastran_time(self, cmd):
        # For Pupiku and Army.
        if cmd not in {"pup", "piku", "army", "daily", "lottery", "cookie"}:
            raise ValueError("Invalid column name.")

        results = await database_handler.get_from_db(
            f"SELECT {cmd} FROM user_stats WHERE user_id = ?",
            (self.client.user.id,),
        )

        if results:
            return results[0][cmd]
        print(
            f"seems like user_stats have not been properly initialised -> {self.client.user.name}"
        )
        return 0

    def update_cmd_lastran_time(self, cmd):
        # For Pupiku and Army.
        if cmd not in {"pup", "piku", "army", "daily", "lottery", "cookie"}:
            raise ValueError("Invalid column name.")

        database_handler.update_database(
            f"UPDATE user_stats SET {cmd} = ? WHERE user_id = ?",
            (self.client.time_in_seconds(), self.client.user.id),
        )

    def update_event_timestamp(self, timestamp):
        # event_till_timestamp
        database_handler.update_database(
            "UPDATE meta_data SET value = ? WHERE key = ?",
            (timestamp, "event_till_timestamp"),
        )

    async def get_event_timestamp(self):
        rows = await database_handler.get_from_db(
            "SELECT value FROM meta_data WHERE key = ?",
            ("event_till_timestamp",),
        )
        return rows[0]["value"]
