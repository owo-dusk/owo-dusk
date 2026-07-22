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

# Standard Library
import os
import signal
import threading

# Third-Party Libraries
import discord
from discord import SyncWebhook

import core.client as client

# Local
import utils.system as syst
from core.bot_runner import fetch_json, run_bots
from utils.captcha_solver.yescaptcha import captchaClient
from utils.constants import owo_dusk_api, owo_panel, version
from utils.database import create_database
from utils.errors import suppress_and_log, suppress_and_log_block
from utils.loader import (
    captcha_settings_dict,
    global_settings_dict,
    misc_dict,
)
from utils.quest_helper.quest import QuestHandler
from utils.runtime_handler import start_runtime_loop
from utils.webhook import webhookSender
from website import web_start


def handle_sigint(signal_number, frame):
    print("\nCtrl+C detected. stopping code!")
    os._exit(0)


@suppress_and_log("Setup Service")
def setup_and_start_services():
    # clear console
    syst.system.clear()

    if not misc_dict["console"]["compactMode"]:
        syst.system.console.print(owo_panel)
        syst.system.console.rule(f"[bold blue1]version - {version}", style="navy_blue")

    # Sets up CTRL+C detection
    signal.signal(signal.SIGINT, handle_sigint)

    # Start battery check service
    syst.battery.start_battery_check()

    # Create database or modify if required
    create_database()

    # Weekly runtime thread
    start_runtime_loop()

    # Start website if enabled
    if global_settings_dict.website.enabled:
        # Start website
        web_thread = threading.Thread(
            target=web_start,
            args=(
                global_settings_dict.website.port,
                global_settings_dict.website.enableHost,
                version,
                global_settings_dict.website.password,
            ),
        )
        web_thread.start()
        # get ip
        ip = syst.system.get_local_ip()
        syst.system.print_box(
            f"Website Dashboard: http://{ip}:{global_settings_dict.website.port}".center(
                syst.system.console_width - 2
            ),
            "dark_magenta",
        )


@suppress_and_log("Version Check")
def notify_version_changes():
    # Detect updates and notify
    version_json = fetch_json(f"{owo_dusk_api}/version.json", "version info")
    if syst.system.compare_versions(version, version_json["version"]):
        syst.system.print_box(
            f"""Update Detected - {version_json["version"]}
    Changelog:
        {version_json["changelog"]}""",
            "bold gold3",
        )
        syst.notification.notify(
            f"Content: {version_json['changelog']}",
            f"New Update detected: {version_json['version']}",
        )
        if version_json["important_update"]:
            syst.system.print_box(
                "It is recommended to update....", "bold light_yellow3"
            )


@suppress_and_log("Ask To Star Repo")
def ask_to_star_repo():
    syst.system.console.print(
        "Won't you take 5~ minutes of your time, from the countless minutes saved by owodusk - to star its GitHub Repo? Thankyou!",
        style="navajo_white1",
    )

    if global_settings_dict.webhook.enabled:
        webhook = SyncWebhook.from_url(global_settings_dict.webhook.webhookUrl)

        color = discord.Color(0xC48DC3)
        emb = discord.Embed(
            title="Star the github repo!",
            description="Starring the GitHub repo motivates us to keep adding new and better features! It takes less than 5 minutes to do that, so do star the GitHub repo at https://github.com/owo-dusk/owo-dusk.",
            color=color,
        )
        emb.set_thumbnail(
            url="https://cdn.discordapp.com/emojis/723856770249916447.gif"
        )

        webhook.send(embed=emb, username="OwO-Dusk")


def start_owodusk():
    syst.notification.notify(
        "OwO-Dusk starting... If any issue arises visit out discord support server (link available in console or github)",
        "Starting OwO-Dusk! :>",
    )
    # Start up tasks and services
    setup_and_start_services()

    # Version Check
    notify_version_changes()

    tokens_and_channels = [
        line.strip().split() for line in open("tokens.txt", "r", encoding="utf-8")
    ]
    token_len = len(tokens_and_channels)

    syst.system.print_box(
        f"-Received {token_len} tokens.".center(syst.system.console_width - 2),
        "bold magenta",
    )

    if misc_dict["news"]:
        with suppress_and_log_block("Fetch News"):
            news_json = fetch_json(f"{owo_dusk_api}/news.json", "news")
            if news_json.get("available"):
                syst.system.print_box(
                    f"{news_json.get('content', 'no content found..? this is an error! should be safe to ignore')}".center(
                        syst.system.console_width - 2
                    ),
                    f"bold {news_json.get('color', 'white')}",
                    title=news_json.get("title", "???"),
                )

    if not misc_dict["console"]["hideStarRepoMessage"]:
        ask_to_star_repo()

    syst.system.console.rule(style="navy_blue")

    client.webhook_handler = webhookSender(global_settings_dict.webhook.webhookUrl)
    client.global_quest_handler = QuestHandler(api=global_settings_dict.ocrApi)
    client.hcaptcha_solver = None
    if (
        captcha_settings_dict["image_solver"]["enabled"]
        or captcha_settings_dict["hcaptcha_solver"]["enabled"]
    ):
        syst.system.console.print(
            "Be Warned, Captcha solving is not well tested.. You are using on your own risk..",
            style="orange_red1",
        )
        if captcha_settings_dict["hcaptcha_solver"]["enabled"]:
            # Setup hcaptcha solver..
            client.hcaptcha_solver = captchaClient(
                captcha_settings_dict["hcaptcha_solver"]["api_key"]
            )
            if client.hcaptcha_solver.balance == 0:
                syst.system.console.print(
                    "Yescaptcha API has no balance...",
                    style="orange_red1",
                )
                os._exit(0)
            else:
                bal = client.hcaptcha_solver.balance
                syst.system.console.print(
                    f"Yescaptcha API has a balance of {bal}, which is approximately {round(bal / 30)} hcaptcha solves.",
                    style="tan",
                )

    if (
        global_settings_dict.captcha.toastOrPopup
        and not syst.system.on_mobile
        and not misc_dict["hostMode"]
    ):
        # In MacOS, for Popup to work correctly, it must be ran through
        # The main loop. For that reason, `run_bots` are ran through a thread
        from utils.system.popup import popup_main_loop

        bot_threads = threading.Thread(target=run_bots, args=(tokens_and_channels,))
        bot_threads.daemon = True
        bot_threads.start()

        popup_main_loop()
    else:
        run_bots(tokens_and_channels)


if __name__ == "__main__":
    start_owodusk()
