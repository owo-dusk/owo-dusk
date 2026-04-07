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

"""
This file contains functions that we use through OwO-Dusk,
but those which is minor to make its own seperate file
"""

from datetime import datetime


"""
Time related
"""


def get_weekday():
    # 0 = monday, 6 = sunday
    return str(datetime.today().weekday())


def get_hour():
    # only from 0 to 23 (24hr format)
    return datetime.now().hour


def get_date():
    return datetime.now().date().isoformat()  # e.g. "2025-05-31"
