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
import sys
import subprocess

from utils.colors import COLORS


def compare_versions(current_version, latest_version):
    current_version = current_version.lstrip("v")
    latest_version = latest_version.lstrip("v")

    current = list(map(int, current_version.split(".")))
    latest = list(map(int, latest_version.split(".")))

    for cur, lat in zip(current, latest):
        if lat > cur:
            return True
        elif lat < cur:
            return False

    if len(latest) > len(current):
        return any(x > 0 for x in latest[len(current) :])

    return False


def clear():
    os.system("cls") if os.name == "nt" else os.system("clear")


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def is_termux():
    termux_prefix = os.environ.get("PREFIX")
    termux_home = os.environ.get("HOME")

    if termux_prefix and "com.termux" in termux_prefix:
        return True
    elif termux_home and "com.termux" in termux_home:
        return True
    else:
        return os.path.isdir("/data/data/com.termux")


def install_package(*args):
    subprocess.check_call([sys.executable, "-m", "pip", "install", *args])


def install_termux_package(package_name: str, display_name: str | None = None):
    name = display_name or package_name

    print(f"{COLORS.BOLD_CYAN}[0]Attempting to install {name}...{COLORS.RESET}")

    try:
        subprocess.check_call(["pkg", "install", package_name, "-y"])
        print(f"{COLORS.BOLD_CYAN}[0]Installed {name} successfully!{COLORS.RESET}")
        return True

    except Exception as e:
        print(
            f"{COLORS.BOLD_RED}[x]Error when trying to install {name}:\n{e}{COLORS.RESET}"
        )
        return False
