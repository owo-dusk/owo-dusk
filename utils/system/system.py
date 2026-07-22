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
import socket
import subprocess
import sys
import threading
import time

try:
    from rich.console import Console
    from rich.panel import Panel

    NO_RICH = False
except ImportError:
    NO_RICH = True

from utils.colors import COLORS
from utils.errors import suppress_and_log

if not NO_RICH:
    from utils.loader import global_settings_dict, misc_dict

    console = Console()
    console.rule("[bold blue1]:>", style="navy_blue")
    console_width = console.size.width
else:
    console = None
    global_settings_dict = None
    misc_dict = None
    console_width = 300


@suppress_and_log("Comparing Version")
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


@suppress_and_log("Getting Resource Path")
def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


@suppress_and_log("Checking if Termux")
def is_termux():
    termux_prefix = os.environ.get("PREFIX")
    termux_home = os.environ.get("HOME")

    if termux_prefix and "com.termux" in termux_prefix:
        return True
    elif termux_home and "com.termux" in termux_home:
        return True
    else:
        return os.path.isdir("/data/data/com.termux")


on_mobile = is_termux()


@suppress_and_log("Installing package")
def install_package(*args):
    subprocess.check_call([sys.executable, "-m", "pip", "install", *args])


@suppress_and_log("Installing Termux Package")
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


@suppress_and_log("Running system command")
def run_system_command(command, timeout, retry=False, delay=5):
    def target():
        try:
            os.system(command)
        except Exception as e:
            print(f"Error executing command: {command} - {e}")

    # Create and start a thread to execute the command
    thread = threading.Thread(target=target)
    thread.start()

    # Wait for the thread to finish, with a timeout
    thread.join(timeout)

    # If the thread is still alive after the timeout, terminate it
    if thread.is_alive():
        print(f"Error: {command} command failed! (captcha)")
        if retry:
            print(f"Retrying '{command}' after {delay}s")
            time.sleep(delay)
            run_system_command(command, timeout)


def print_box(text, color, title=None):
    if NO_RICH:
        print("rich is unavailable, please recheck your installation!")
        return

    test_panel = Panel(text, style=color, title=title)
    if not misc_dict["console"]["compactMode"]:
        console.print(test_panel)
    else:
        console.print(text, style=color)


def get_local_ip():
    if NO_RICH:
        print("rich is unavailable, please recheck your installation!")
        return None

    if not global_settings_dict.website.enableHost:
        return "localhost"
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            """10.255.255.255 is fake"""
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
    except Exception:
        return "localhost"
