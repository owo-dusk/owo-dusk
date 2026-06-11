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

from datetime import datetime, timezone, timedelta


def current_timestamp():
    return datetime.now(timezone.utc)


def is_month_over(recorded_at: datetime) -> bool:
    now = datetime.now(timezone.utc)

    # Tuple comparison is soo cool!
    return (now.year, now.month) > (recorded_at.year, recorded_at.month)


def discord_timestamp_to_datetime(unix_timestamp: int) -> datetime:
    return datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)


def calc_time_till_event(initial_timestamp: datetime) -> datetime:
    return datetime + timedelta(days=7)


def get_weekday():
    # 0 = monday, 6 = sunday
    return str(datetime.today().weekday())


def get_hour():
    # only from 0 to 23 (24hr format)
    return datetime.now().hour


def get_date():
    return datetime.now().date().isoformat()  # e.g. "2025-05-31"


def validate_snowflake(snowflake: str):
    """
    Accepts a snowflake (channel/guild) and validates it
    The aim is not to ensure the id is valid, but to rather
    ensure obviously not correct ids are filtered out
    """
    return snowflake.isdigit() and 16 <= len(snowflake) <= 20


def calc_time_till_timestamp(timestamp: datetime):
    return (timestamp - datetime.now(tz=timezone.utc)).total_seconds()
