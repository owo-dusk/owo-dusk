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

import time
import re
import os
import sys
import asyncio
import tomllib

from discord.ext import commands, tasks
from discord import DMChannel

from utils.misc import is_termux, run_system_command
from utils.notification import notify
from utils.timestamp import validate_snowflake
from cogs._BASE import BaseCog


list_captcha = ["human", "captcha", "link", "letterword"]


def get_path(path):
    cur_dir = os.getcwd()
    if os.path.isfile(path):
        """See if complete path"""
        return path
    audio_folder_path = os.path.join(cur_dir, "audio", path)
    if os.path.isfile(audio_folder_path):
        """See if audio file is in audio folder"""
        return audio_folder_path
    file_in_cwd = os.path.join(cur_dir, path)
    if os.path.isfile(file_in_cwd):
        """See if audio file is in working directory"""
        return file_in_cwd
    """None otherwise"""
    return None


def clean(msg):
    return re.sub(r"[^a-zA-Z0-9]", "", msg)


on_mobile = is_termux()

if not on_mobile:
    # desktop
    from playsound3 import playsound


def load_json_dict(file_path="config/captcha.toml"):
    with open(file_path, "rb") as config_file:
        return tomllib.load(config_file)


cap_cnf_dict = load_json_dict()

if cap_cnf_dict:
    if cap_cnf_dict["image_solver"]["enabled"]:
        from utils.captcha_solver.image_captcha import solveImageCaptcha


def get_channel_name(channel):
    if isinstance(channel, DMChannel):
        return "owo DMs"
    return channel.name


def console_handler(cnf, captcha=True):
    # If captcha flag set to False, Ban command will be ran
    if cnf.onCaptcha and captcha:
        run_system_command(cnf.captchaCommand, timeout=5)
    elif cnf.onBan and not captcha:
        run_system_command(cnf.banCommand, timeout=5)


def get_reccur_sleep_time(times_to_reccur):
    if times_to_reccur > 600:
        # I wonder what would hapeen without this check.
        return 200
    return 600 / times_to_reccur


class Captcha(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.sound = None
        self.reccured = 0
        self.content_to_notify = ""
        self.kill_task = None
        self.yescaptcha_in_progress = False
        self.captcha_site_opened = False

    def fetch_settings(self, cmd):
        return getattr(self.bot.settings_dict.commands, cmd)

    @property
    def captcha_settings(self):
        return self.bot.global_settings_dict.captcha

    @property
    def notification_settings(self):
        return self.captcha_settings.notifications

    @property
    def toast_settings(self):
        return self.captcha_settings.toastOrPopup

    @property
    def termux_settings(self):
        return self.captcha_settings.termux

    @property
    def webhook_settings(self):
        return self.bot.global_settings_dict.webhook

    def get_webhook(self):
        webhook_url = self.webhook_settings.webhookCaptchaUrl
        if not isinstance(webhook_url, str):
            # Ensure webhook url is valid
            webhook_url = None
        elif "discord.com" not in webhook_url:
            # Only accept discord webhook.
            print(f"webhook Url {webhook_url} seems invalid")
            webhook_url = None
        return webhook_url

    async def kill_code(self):
        await asyncio.sleep(590)
        if self.bot.command_handler_status["captcha"]:
            print("captcha not solved within time...")
            os._exit(0)

    @tasks.loop()
    async def reccur_notifications(self):
        if self.content_to_notify:
            notify(self.content_to_notify, f"Captcha - {self.bot.username}!")
            self.reccured += 1

        times_to_reccur = self.notification_settings.reccur.timesToReccur

        if self.reccured == times_to_reccur:
            self.reccur_notifications.cancel()

        await asyncio.sleep(get_reccur_sleep_time(times_to_reccur))

    def captcha_handler(self, channel, captcha_type):
        if self.bot.misc["hostMode"]:
            return
        channel_name = get_channel_name(channel)
        content_type = (
            "captchaContent" if not captcha_type == "Ban" else "bannedContent"
        )
        url = "https://owobot.com/captcha"

        """Notifications"""
        if self.notification_settings.enabled:
            notification_content = getattr(
                self.notification_settings, content_type
            ).format(
                username=self.bot.username,
                channelname=channel_name,
                captchatype=captcha_type,
            )

            if self.notification_settings.reccur.enabled:
                self.reccured = 0
                self.content_to_notify = notification_content
                try:
                    self.reccur_notifications.start()
                except Exception:
                    # In case code sends one command after captcha, triggering captcha message twice.
                    pass
            else:
                try:
                    notify(notification_content, f"Captcha - {self.bot.username}!")
                except Exception as e:
                    print(f"{e} - at notifs")

        """Play audio file"""
        """
        TASK: add two checks, check the path for the file in both outside utils folder
        and in owo-dusk folder
        +
        better error handling for missing PATH
        """
        if self.captcha_settings.playAudio.enabled:
            path = get_path(self.captcha_settings.playAudio.path)
            try:
                if on_mobile:
                    run_system_command(
                        f"termux-media-player play {path}", timeout=5, retry=True
                    )
                else:
                    self.sound = playsound(path, block=False)
            except Exception as e:
                print(f"{e} - at audio")
        """Toast/Popup"""
        if self.toast_settings.enabled:
            try:
                if on_mobile:
                    settings = self.toast_settings.termuxToast
                    run_system_command(
                        f"termux-toast -c {settings.textColour} -b {settings.backgroundColour} -g {settings.position} '{getattr(self.toast_settings, content_type).format(username=self.bot.username, channelname=channel_name, captchatype=captcha_type)}'",
                        timeout=5,
                        retry=True,
                    )
                else:
                    self.bot.add_popup_queue(channel_name, captcha_type)
            except Exception as e:
                print(f"{e} - at Toast/Popup")
        """Termux - Vibrate"""
        if self.termux_settings.vibrate.enabled:
            try:
                if on_mobile:
                    run_system_command(
                        f"termux-vibrate -f -d {self.termux_settings.vibrate.time * 1000}",
                        timeout=5,
                        retry=True,
                    )
                else:
                    pass
            except Exception as e:
                print(f"{e} - at Toast/Popup")
        """Termux - TTS"""
        if self.termux_settings.textToSpeech.enabled:
            try:
                if on_mobile:
                    run_system_command(
                        f"termux-tts-speak {getattr(self.termux_settings.textToSpeech, content_type)}",
                        timeout=7,
                        retry=False,
                    )
                else:
                    pass
            except Exception as e:
                print(f"{e} - at Toast/Popup")
        """Open captcha website"""
        if self.captcha_settings.openCaptchaWebsite and not self.captcha_site_opened:
            if on_mobile:
                run_system_command(f"termux-open {url}", timeout=5, retry=True)
            else:
                if sys.platform.startswith("win"):
                    run_system_command(f"start {url}", timeout=5, retry=True)
                elif sys.platform == "darwin":
                    # Macos
                    run_system_command(f"open {url}", timeout=5, retry=True)
                else:
                    # Linux
                    run_system_command(f"xdg-open {url}", timeout=5, retry=True)
            self.captcha_site_opened = True

    async def handle_solves(self):
        if self.bot.misc["hostMode"]:
            return

        """Play Audio"""
        if self.captcha_settings.playAudio.enabled:
            try:
                if on_mobile:
                    run_system_command(
                        "termux-media-player stop", timeout=5, retry=True
                    )
                else:
                    if self.sound is not None:
                        if self.sound.is_alive():
                            self.sound.stop()
            except Exception as e:
                print(f"{e} - at audio")

        """Reccurrring notification"""
        if (
            self.notification_settings.enabled
            and self.notification_settings.reccur.enabled
        ):
            try:
                self.reccur_notifications.cancel()
            except Exception:
                pass

        if self.captcha_settings.stopIfFailure:
            if not self.kill_task.done():
                self.kill_task.cancel()

    @commands.Cog.listener()
    async def on_message(self, message):
        self.last_msg = time.time()

        # This is likely a part of temporary fix, I forgot.
        # Doesn't hurt letting it stay!
        if not self.bot.dm:
            if message.author.id == self.bot.owo_bot_id:
                self.bot.dm = await message.author.create_dm()
            else:
                # Safe, since only owobot will send captcha messages.
                return

        if (
            message.channel.id == self.bot.dm.id
            and message.author.id == self.bot.owo_bot_id
        ):
            if "I have verified that you are human! Thank you! :3" in message.content:
                time_to_sleep = self.bot.random_float(
                    self.bot.settings_dict.cooldowns.captchaRestart
                )
                await self.bot.log(
                    f"Captcha solved! - sleeping {time_to_sleep}s before restart.",
                    "#5fd700",
                )
                await asyncio.sleep(time_to_sleep)
                self.bot.command_handler_status["captcha"] = False
                self.bot.db.update_captcha_db()
                await self.handle_solves()
                self.captcha_site_opened = False
                if self.webhook_settings.enabled:
                    await self.bot.send_webhook(
                        "on_captcha_solve",
                        webhook_url=self.get_webhook(),
                        captcha_url=message.jump_url,
                        pingid=(
                            self.webhook_settings.pingUserId
                            if validate_snowflake(self.webhook_settings.pingUserId)
                            else None
                        ),
                    )
                return

        channels = [self.bot.dm.id, self.bot.cm.id, self.bot.boss_channel_id]

        for cmd in ("pray", "curse"):
            cnf = self.fetch_settings(cmd).custom_channel
            if cnf.enabled:
                channels.append(cnf.channel)

        if message.channel.id in channels and message.author.id == self.bot.owo_bot_id:
            components = message.components
            content = clean(message.content)
            # Checks if `Verify` button exists
            has_verify_button = (
                components
                and components[0].children
                and getattr(components[0].children[0], "label", None) == "Verify"
            )

            has_warning_attachment = "⚠️" in message.content and message.attachments

            contains_captcha_word = any(word in content for word in list_captcha)

            if has_verify_button or has_warning_attachment or contains_captcha_word:
                nick = self.bot.get_nick(message)

                if not get_channel_name(message.channel) == "owo DMs":
                    if not any(
                        user in message.content
                        for user in (
                            self.bot.user.name,
                            f"<@{self.bot.user.id}>",
                            nick,
                            self.bot.user.display_name,
                        )
                    ):
                        return
                self.bot.command_handler_status["captcha"] = True
                await self.bot.log("Captcha detected!", "#d70000")
                image_captcha = False
                if message.attachments:
                    image_captcha = True
                cap_dict = self.bot.captcha_settings_dict

                if self.captcha_settings.stopIfFailure:
                    """Kill code if failure in solving captcha within time"""
                    self.kill_task = asyncio.create_task(self.kill_code())

                if cap_dict["notifications"]["notify_when_attempting_to_solve"] or not (
                    cap_dict["hcaptcha_solver"]["enabled"]
                    or cap_dict["image_solver"]["enabled"]
                ):
                    self.captcha_handler(message.channel, "Link")
                elif (image_captcha and not cap_dict["image_solver"]["enabled"]) or (
                    not image_captcha and not cap_dict["hcaptcha_solver"]["enabled"]
                ):
                    self.captcha_handler(message.channel, "Link")

                if self.webhook_settings.enabled:
                    await self.bot.send_webhook(
                        "on_captcha",
                        webhook_url=self.get_webhook(),
                        captcha_url=message.jump_url,
                        pingid=(
                            self.webhook_settings.pingUserId
                            if validate_snowflake(self.webhook_settings.pingUserId)
                            else None
                        ),
                    )
                console_handler(self.bot.global_settings_dict.console)

                if cap_dict["hcaptcha_solver"]["enabled"] and not image_captcha:
                    if not self.yescaptcha_in_progress:
                        self.yescaptcha_in_progress = True
                        await self.bot.log("Attempting to solve hcaptcha", "#656b66")
                        solved = await self.bot.captcha_handler.solve_owo_bot_captcha(
                            self.bot.local_headers,
                            cap_dict["hcaptcha_solver"]["retries"],
                        )
                        if not solved:
                            await self.bot.log("FAILED to solve hcaptcha", "#d70000")
                            self.captcha_handler(message.channel, "Link")
                            print("stopping code.... Reason -> Failed Hcaptcha attempt")
                            if self.webhook_settings.enabled:
                                await self.bot.send_webhook(
                                    "on_captcha_solve_fail",
                                    webhook_url=self.get_webhook(),
                                    pingid=(
                                        self.webhook_settings.pingUserId
                                        if validate_snowflake(
                                            self.webhook_settings.pingUserId
                                        )
                                        else None
                                    ),
                                )
                            os._exit(0)
                        else:
                            balance = self.bot.captcha_handler.balance
                            solves_left = balance // 30

                            await self.bot.log(
                                f"solved, {solves_left} solves left (balance: {balance})",
                                "#d70000",
                            )

                            if solves_left < 1:
                                self.bot.command_handler_status["captcha"] = True
                                await self.bot.log(
                                    f"credits exhausted - balance: {balance}, stopping...",
                                    "#d70000",
                                )
                                if self.webhook_settings.enabled:
                                    await self.bot.send_webhook(
                                        "on_captcha_solve_no_credits",
                                        webhook_url=self.get_webhook(),
                                        pingid=(
                                            self.webhook_settings.pingUserId
                                            if validate_snowflake(
                                                self.webhook_settings.pingUserId
                                            )
                                            else None
                                        ),
                                    )
                                os._exit(0)
                        self.yescaptcha_in_progress = False

                elif cap_dict["image_solver"]["enabled"] and image_captcha:
                    await self.bot.log("Attempting to solve image captcha", "#656b66")
                    letters = int(
                        re.findall(
                            r"(\d+)(?=letterword)", clean(message.content.lower())
                        )[0]
                    )
                    ans = await solveImageCaptcha(
                        message.attachments[0].url, letters, self.bot.session
                    )
                    if ans:
                        await self.bot.log(
                            f"answer of image captcha -> {ans}", "#656b66"
                        )
                        await message.author.send(ans)

            elif (
                "You have been banned for" in message.content
                and self.bot.user.name in message.content
            ):
                self.bot.command_handler_status["captcha"] = True
                await self.bot.log("Ban detected!", "#d70000")
                self.captcha_handler(message.channel, "Ban")
                console_handler(self.bot.global_settings_dict.console, captcha=False)
                if self.webhook_settings.enabled:
                    await self.bot.send_webhook(
                        "on_captcha_ban",
                        webhook_url=self.get_webhook(),
                        captcha_url=message.jump_url,
                        pingid=(
                            self.webhook_settings.pingUserId
                            if validate_snowflake(self.webhook_settings.pingUserId)
                            else None
                        ),
                    )


async def setup(bot):
    await bot.add_cog(Captcha(bot))
