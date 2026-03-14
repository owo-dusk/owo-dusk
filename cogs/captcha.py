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
    if cnf["runConsoleCommandOnCaptcha"] and captcha:
        run_system_command(cnf["commandToRunOnCaptcha"], timeout=5)
    elif cnf["runConsoleCommandOnBan"] and not captcha:
        run_system_command(cnf["commandToRunOnBan"], timeout=5)


def get_reccur_sleep_time(times_to_reccur):
    if times_to_reccur > 600:
        # I wonder what would hapeen without this check.
        return 200
    return 600 / times_to_reccur


class Captcha(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sound = None
        self.reccured = 0
        self.content_to_notify = ""
        self.kill_task = None
        self.solve_in_progress = False
        self.captcha_solved = False

    async def kill_code(self):
        await asyncio.sleep(590)
        if self.bot.command_handler_status["captcha"]:
            print("captcha not solved within time...")
            os._exit(0)

    async def captcha_handler(self, channel, captcha_type):
        if self.bot.misc["hostMode"]:
            return
        cnf = self.bot.global_settings_dict["captcha"]
        if not cnf["notifications"]["reccur"]["enabled"]:
            await self.handle_once(channel, captcha_type)
            return

        times_to_reccur = cnf["notifications"]["reccur"]["times_to_reccur"]

        for _ in range(times_to_reccur):
            if self.captcha_solved:
                break

            await self.handle_once(channel, captcha_type)
            await asyncio.sleep(get_reccur_sleep_time(times_to_reccur))

    async def handle_once(self, channel, captcha_type):
        cnf = self.bot.global_settings_dict["captcha"]
        channel_name = get_channel_name(channel)
        content = "captchaContent" if not captcha_type == "Ban" else "bannedContent"
        url = "https://owobot.com/captcha"

        """Notifications"""
        if cnf["notifications"]["enabled"]:
            notification_content = cnf["notifications"][content].format(
                username=self.bot.username,
                channelname=channel_name,
                captchatype=captcha_type,
            )
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
        if cnf["playAudio"]["enabled"]:
            path = get_path(cnf["playAudio"]["path"])
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
        if cnf["toastOrPopup"]["enabled"]:
            try:
                if on_mobile:
                    run_system_command(
                        f"termux-toast -c {cnf['toastOrPopup']['termuxToast']['textColour']} -b {cnf['toastOrPopup']['termuxToast']['backgroundColour']} -g {cnf['toastOrPopup']['termuxToast']['position']} '{cnf['toastOrPopup'][content].format(username=self.bot.username, channelname=channel_name, captchatype=captcha_type)}'",
                        timeout=5,
                        retry=True,
                    )
                else:
                    self.bot.add_popup_queue(channel_name, captcha_type)
            except Exception as e:
                print(f"{e} - at Toast/Popup")
        """Termux - Vibrate"""
        if cnf["termux"]["vibrate"]["enabled"]:
            try:
                if on_mobile:
                    run_system_command(
                        f"termux-vibrate -f -d {cnf['termux']['vibrate']['time'] * 1000}",
                        timeout=5,
                        retry=True,
                    )
                else:
                    pass
            except Exception as e:
                print(f"{e} - at Toast/Popup")
        """Termux - TTS"""
        if cnf["termux"]["textToSpeech"]["enabled"]:
            try:
                if on_mobile:
                    run_system_command(
                        f"termux-tts-speak {cnf['termux']['textToSpeech'][content]}",
                        timeout=7,
                        retry=False,
                    )
                else:
                    pass
            except Exception as e:
                print(f"{e} - at Toast/Popup")
        """Termux - open captcha website"""
        if cnf["openCaptchaWebsite"]:
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

    async def handle_solves(self):
        if self.bot.misc["hostMode"]:
            return
        cnf = self.bot.global_settings_dict["captcha"]
        self.captcha_solved = True

        """Play Audio"""
        if cnf["playAudio"]["enabled"]:
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

        if cnf["stopCodeIfFailedToSolve"]:
            if not self.kill_task.done():
                self.kill_task.cancel()

        if self.bot.global_settings_dict["webhook"]["enabled"]:
            await self.bot.webhookSender(
                title=f"-{self.bot.username} - Captcha Solved",
                desc=f"**User** <@{self.bot.user.id}> solved captcha successfully!",
                colors="#00FFAF",
                img_url="https://cdn.discordapp.com/emojis/1090553827847045160.gif",
                author_img_url="https://i.imgur.com/6zeCgXo.png",
                webhook_url=self.bot.global_settings_dict["webhook"].get(
                    "webhookCaptchaUrl", None
                ),
            )

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
                time_to_sleep = round(self.bot.random_float(
                    self.bot.settings_dict["defaultCooldowns"]["captchaRestart"]), 2)
                await self.bot.log(
                    f"Captcha solved! - sleeping {time_to_sleep}s before restart.",
                    "#5fd700",
                )
                await asyncio.sleep(time_to_sleep)
                self.bot.command_handler_status["captcha"] = False
                self.bot.update_captcha_db()
                await self.handle_solves()
                return

        channels = [self.bot.dm.id, self.bot.cm.id, self.bot.boss_channel_id]
        if self.bot.settings_dict["commands"]["pray"]["customChannel"]["enabled"]:
            channels.append(
                self.bot.settings_dict["commands"]["pray"]["customChannel"]["channelId"]
            )
        if self.bot.settings_dict["commands"]["curse"]["customChannel"]["enabled"]:
            channels.append(
                self.bot.settings_dict["commands"]["curse"]["customChannel"][
                    "channelId"
                ]
            )

        if message.channel.id in channels and message.author.id == self.bot.owo_bot_id:
            """Handle normally expected captcha"""
            if (
                (
                    message.components
                    and len(message.components) > 0
                    and hasattr(message.components[0], "children")
                    and len(message.components[0].children) > 0
                    and (
                        (
                            hasattr(message.components[0].children[0], "label")
                            and message.components[0].children[0].label == "Verify"
                        )
                        or (
                            hasattr(message.components[0].children[0], "url")
                            and message.components[0].children[0].url
                            == "https://owobot.com?login="
                        )
                    )
                )
                or (
                    "⚠️" in message.content and message.attachments
                )  # message attachment check
                or any(b in clean(message.content) for b in list_captcha)
            ):
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
                self.captcha_solved = False
                await self.bot.log("Captcha detected!", "#d70000")
                if not message.attachments:
                    image_captcha = False
                    captcha_type = "Link"
                else:
                    image_captcha = True
                    captcha_type = "Letter Word"
                cap_dict = self.bot.captcha_settings_dict
                cnf = self.bot.global_settings_dict["captcha"]

                if cnf["stopCodeIfFailedToSolve"]:
                    """Kill code if failure in solving captcha within time"""
                    self.kill_task = asyncio.create_task(self.kill_code())

                if cap_dict["notifications"]["notify_when_attempting_to_solve"] or not (
                    cap_dict["hcaptcha_solver"]["enabled"]
                    or cap_dict["image_solver"]["enabled"]
                ):
                    await self.captcha_handler(message.channel, captcha_type)
                elif (image_captcha and not cap_dict["image_solver"]["enabled"]) or (
                    not image_captcha and not cap_dict["hcaptcha_solver"]["enabled"]
                ):
                    await self.captcha_handler(message.channel, captcha_type)

                if self.bot.global_settings_dict["webhook"]["enabled"]:
                    await self.bot.webhookSender(
                        title=f"-{self.bot.username} - CAPTCHA Detected",
                        desc=f"**User** : <@{self.bot.user.id}>\n**Link** : [OwO Captcha]({message.jump_url})",
                        colors="#CF5319",
                        img_url="https://cdn.discordapp.com/emojis/755106539122982922.gif",
                        author_img_url="https://i.imgur.com/6zeCgXo.png",
                        msg=(
                            f"<@{self.bot.global_settings_dict['webhook']['webhookUserIdToPingOnCaptcha']}>"
                            if self.bot.global_settings_dict["webhook"][
                                "webhookUserIdToPingOnCaptcha"
                            ]
                            else None
                        ),
                        webhook_url=self.bot.global_settings_dict["webhook"].get(
                            "webhookCaptchaUrl", None
                        ),
                    )
                console_handler(self.bot.global_settings_dict["console"])

                if cap_dict["hcaptcha_solver"]["enabled"] and not image_captcha:
                    if not self.solve_in_progress:
                        self.solve_in_progress = True
                        await self.bot.log("Attempting to solve hcaptcha", "#656b66")
                        solved = await self.bot.captcha_handler.solve_owo_bot_captcha(
                            self.bot.local_headers,
                            cap_dict["hcaptcha_solver"]["retries"]
                        )
                        if not solved:
                            await self.bot.log("FAILED to solve hcaptcha", "#d70000")
                            self.captcha_handler(message.channel, captcha_type)
                            print("stopping code.... Reason -> Failed Hcaptcha attempt")
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
                                os._exit(0)
                        self.solve_in_progress = False

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

            elif "You have been banned for" in message.content:
                self.bot.command_handler_status["captcha"] = True
                await self.bot.log("Ban detected!", "#d70000")
                self.captcha_handler(message.channel, "Ban")
                console_handler(self.bot.global_settings_dict["console"], captcha=False)
                if self.bot.global_settings_dict["webhook"]["enabled"]:
                    await self.bot.webhookSender(
                        title=f"-{self.bot.username} - BAN Detected",
                        desc=f"**User** : <@{self.bot.user.id}>\n**Link** : [Ban Message]({message.jump_url})",
                        colors="#00FFAF",
                        img_url="https://cdn.discordapp.com/emojis/1068981158081216662.gif",
                        author_img_url="https://i.imgur.com/6zeCgXo.png",
                        msg=(
                            f"<@{self.bot.global_settings_dict['webhook']['webhookUserIdToPingOnCaptcha']}>"
                            if self.bot.global_settings_dict["webhook"][
                                "webhookUserIdToPingOnCaptcha"
                            ]
                            else None
                        ),
                        webhook_url=self.bot.global_settings_dict["webhook"].get(
                            "webhookCaptchaUrl", None
                        ),
                    )


async def setup(bot):
    await bot.add_cog(Captcha(bot))
