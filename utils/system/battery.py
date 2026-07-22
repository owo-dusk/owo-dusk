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

import json
import os
import threading
import time

from utils.errors import suppress_and_log, suppress_and_log_block
from utils.loader import global_settings_dict, misc_dict
from utils.system.system import console, console_width, on_mobile

psutil = None

if not on_mobile and not misc_dict["hostMode"]:
    with suppress_and_log_block("Importing Battery Check"):
        if global_settings_dict.batteryCheck.enabled:
            import psutil


# For battery check
@suppress_and_log("Battery Checker")
def check_battery():
    cnf = global_settings_dict.batteryCheck
    if on_mobile:
        while True:
            time.sleep(cnf.refreshInterval)

            battery_status = os.popen("termux-battery-status").read()
            battery_data = json.loads(battery_status)
            percentage = battery_data["percentage"]
            console.print(
                f"Current battery •> {percentage}".center(console_width - 2),
                style="blue ",
            )
            if percentage < int(cnf.minPercentage):
                break
    else:
        while True:
            time.sleep(cnf.refreshInterval)
            battery = psutil.sensors_battery()
            if battery is not None:
                percentage = int(battery.percent)
                console.print(
                    f"Current battery •> {percentage}".center(console_width - 2),
                    style="blue ",
                )
                if percentage < int(cnf.minPercentage):
                    break


def start_battery_check():
    if global_settings_dict.batteryCheck.enabled:
        loop_thread = threading.Thread(target=check_battery, daemon=True)
        loop_thread.start()
