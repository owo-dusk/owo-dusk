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

import asyncio
import json
import os
import random
import threading
import traceback
from datetime import datetime, timedelta, timezone

# Third-Party Libraries
import aiohttp
import discord
import pytz
from discord.ext import commands, tasks

# Local
import core.command_handler as command_handler
import core.components as components
import core.database as database
import utils.config_models as config_models
import utils.system as syst
from utils.constants import owo_dusk_api, version
from utils.errors import suppress_and_log, suppress_and_log_block
from utils.loader import (
    captcha_settings_dict,
    danger_settings_dict,
    global_settings_dict,
    webhook_data_dict,
)
from utils.misspell import misspell_word
from utils.quest_helper.quest import LocalQuestHandler
from website import website_append

list_user_ids = []
webhook_handler = None
hcaptcha_solver = None
global_quest_handler = None
lock = threading.Lock()


class MessageDispatcher:
    """
    This is used like a middle man between on_socket_raw_receive and
    receiver functions
    """

    def __init__(self):
        self._message_handlers = []
        self._edit_handlers = []

    def register(self, func, edit=False):
        if not edit:
            self._message_handlers.append(func)
        else:
            self._edit_handlers.append(func)

    async def dispatch_on_message(self, message):
        for func in self._message_handlers:
            await func(message)

    async def dispatch_on_edit(self, message):
        for func in self._edit_handlers:
            await func(message)


class Stats:
    """
    This tracks certain required statistics like cowoncy
    """

    def __init__(self):
        # Cowoncy Tracker
        self.balance = 0  # current cowoncy
        self.net_earnings = 0  # loss/gain of cowoncy
        self.has_updated_balance = False
        # Gambling Tracker
        self.gain_or_lose = 0
        # Gems
        self.no_gem = False


class MyClient(commands.Bot):
    def __init__(
        self, token, channel_id, global_settings_dict, token_len, *args, **kwargs
    ):
        super().__init__(
            command_prefix="-", self_bot=True, enable_debug_events=True, *args, **kwargs
        )
        self.token = token
        self.boss_channel_id = 0
        self.token_len = token_len
        self.channel_id = int(channel_id)
        self.list_channel = [self.channel_id]
        self.session = None
        self.message_dispatcher = MessageDispatcher()
        self.settings_dict = None
        self.global_settings_dict = global_settings_dict
        self.captcha_settings_dict = captcha_settings_dict
        self.commands_dict = {}
        self.dm, self.cm = None, None
        self.hunt_disabled = False
        self.username = None
        self.nick_name = None
        self.reaction_bot_id = 519287796549156864
        self.owo_bot_id = 408785106942164992
        self.captcha_handler = hcaptcha_solver
        self.db = database.Database(self)
        self.quest_handler = None
        self.danger_settings_dict = danger_settings_dict
        self.stats = Stats()
        if not syst.system.on_mobile:
            self.add_popup_queue = syst.popup.add_popup_queue
        else:
            # Shouldn't be used on Termux Devices...
            self.add_popup_queue = None

        self.quest_help_request = {
            "cookie": {"till": 0, "enabled": False, "userid": 0, "channel": 0},
            "pray": {"till": 0, "enabled": False, "userid": 0, "channel": 0},
            "curse": {"till": 0, "enabled": False, "userid": 0, "channel": 0},
            "battle": {"till": 0, "enabled": False, "userid": 0, "channel": 0},
        }
        self.ongoing_battle_external_quest = False

        # For sell/sac to know the rank of animals caught from hunt to dynamically handle them
        # Updated through hunt.py Cog.
        self.animal_rank_in_zoo = {
            "common": False,
            "uncommon": False,
            "rare": False,
            "epic": False,
            "special": False,
            "mythical": False,
            "gem": False,
            "legendary": False,
            "fabled": False,
            "distorted": False,
            "hidden": False,
        }

        # discord.py-self's module sets global random to fixed seed. reset that, locally.
        self.random = random.Random()

        self.ongoing_owobot_event = False

        with open("config/misc.json", "r", encoding="utf-8") as config_file:
            self.misc = json.load(config_file)

        self.ch = command_handler.CommandHandler(self)

        self.alias = self.misc["alias"]

    async def on_socket_raw_receive(self, msg):
        """
        Raw socket messages from Discord.py-self comes over here.
        """

        parsed_msg = json.loads(msg)
        if parsed_msg.get("t") not in ["MESSAGE_CREATE", "MESSAGE_UPDATE"]:
            return

        message = components.message.get_message_obj(parsed_msg["d"])

        if parsed_msg["t"] == "MESSAGE_CREATE":
            await self.message_dispatcher.dispatch_on_message(message)
        else:
            await self.message_dispatcher.dispatch_on_edit(message)

    @property
    def active_channel_ids(self):
        ids = set()
        if self.cm:
            ids.add(self.cm.id)
        if self.dm:
            ids.add(self.dm.id)
        if self.boss_channel_id:
            ids.add(self.boss_channel_id)
        if self.settings_dict:
            for cmd_name in ("pray", "curse"):
                cnf = getattr(self.settings_dict.commands, cmd_name, None)
                custom = getattr(cnf, "custom_channel", None) if cnf else None
                if custom and custom.enabled:
                    ids.add(custom.channel)
        return ids

    async def empty_checks_and_switch(self, channel):
        self.ch.command_handler_status.hold_handler = True
        await self.sleep_till(
            self.global_settings_dict.channelSwitcher.delayBeforeSwitch
        )
        self.cm = channel
        self.channel_id = self.cm.id
        self.ch.command_handler_status.hold_handler = False

    @tasks.loop(seconds=30)
    async def presence(self):
        if self.status != discord.Status.invisible:
            try:
                await self.change_presence(
                    status=discord.Status.invisible, activity=self.activity
                )
                self.presence.stop()
            except Exception:
                pass
        else:
            self.presence.stop()

    @tasks.loop(seconds=1)
    async def random_sleep(self):
        sleep_obj = self.settings_dict.sleep
        await asyncio.sleep(sleep_obj.get_check_time())
        if sleep_obj.should_sleep():
            await self.ch.set_stat(False)
            sleep_time = sleep_obj.get_sleep_time()
            await self.log(f"sleeping for {sleep_time}", "#87af87")
            await asyncio.sleep(sleep_time)
            await self.ch.set_stat(True)
            await self.log("sleeping finished!", "#87af87")

    @tasks.loop(seconds=7)
    async def safety_check_loop(self):
        if not self.session:
            return
        timeout = aiohttp.ClientTimeout(total=10)
        try:
            async with self.session.get(
                f"{owo_dusk_api}/safety_check.json", timeout=timeout
            ) as resp:
                safety_check = await resp.json()
            async with self.session.get(
                f"{owo_dusk_api}/version.json", timeout=timeout
            ) as resp:
                latest_version = await resp.json()
        except Exception as e:
            await self.log(
                f"Safety check request failed, will retry next cycle: {e}",
                "#5c0018",
            )
            return
        if syst.system.compare_versions(version, safety_check["version"]):
            self.ch.command_handler_status.captcha = True
            await self.log(
                f"There seems to be something wrong...\nStopping code for reason: {safety_check['reason']}\n(This was triggered by {safety_check['author']})",
                "#5c0018",
            )
            if syst.system.compare_versions(
                latest_version["version"], safety_check["version"]
            ):
                await self.log(
                    f"please update to: v{latest_version['version']} to continue using owo-dusk!",
                    "#33245e",
                )

    async def start_cogs(self):
        files = os.listdir(
            syst.system.resource_path("./core/cogs")
        )  # Get the list of files
        self.random.shuffle(files)
        self.refresh_commands_dict()
        with suppress_and_log_block("Starting Cog"):
            for filename in files:
                if filename.endswith(".py"):
                    extension = f"core.cogs.{filename[:-3]}"
                    if extension in self.extensions:
                        """skip if already loaded"""
                        self.refresh_commands_dict()
                        if not self.commands_dict[str(filename[:-3])]:
                            await self.unload_cog(extension)
                        continue

                    await self.sleep_till(
                        self.global_settings_dict.account.commandsStart
                    )
                    if self.commands_dict.get(str(filename[:-3]), False):
                        await self.load_extension(extension)

        if "core.cogs.captcha" not in self.extensions:
            await self.log(
                "Error - Failed to load captcha extension,\nStopping code!!", "#c25560"
            )
            os._exit(0)

    async def update_config(self):
        async with self.lock:
            custom_path = f"config/{self.user.id}.settings.json"
            default_config_path = "config/settings.json"

            config_path = (
                custom_path if os.path.exists(custom_path) else default_config_path
            )

            with open(config_path, "r", encoding="utf-8") as config_file:
                self.settings_dict = config_models.configs.FetchSettings(
                    json.load(config_file)
                )

            await self.start_cogs()

    @suppress_and_log("Unloading Cog")
    async def unload_cog(self, cog_name):
        if cog_name in self.extensions:
            await self.unload_extension(cog_name)

    def refresh_commands_dict(self):
        commands_obj = self.settings_dict.commands
        reaction_bot_obj = self.settings_dict.cooldowns.reactionBot
        gamble_obj = self.settings_dict.gamble

        # Reaction Bot:
        if (
            (
                reaction_bot_obj.huntAndBattle
                and (commands_obj.hunt.enabled or commands_obj.battle.enabled)
            )
            or (reaction_bot_obj.owo and commands_obj.owo.enabled)
            or reaction_bot_obj.prayAndCurse
            and (commands_obj.pray.enabled or commands_obj.curse.enabled)
        ):
            reactionbot = True
        else:
            reactionbot = False

        should_start_looper = (
            # owo
            (commands_obj.owo.enabled and not reaction_bot_obj.owo)
            # pray/curse
            or (
                (commands_obj.pray.enabled or commands_obj.curse.enabled)
                and not reaction_bot_obj.prayAndCurse
            )
            # level grind
            or commands_obj.lvlGrind.enabled
        )

        self.commands_dict = {
            "army": commands_obj.army.enabled,
            "battle": commands_obj.battle.enabled
            and not reaction_bot_obj.huntAndBattle,
            "blackjack": gamble_obj.blackjack.enabled,
            "boss": self.settings_dict.boss.enabled,
            "captcha": True,
            "channelswitcher": self.global_settings_dict.channelSwitcher.enabled,
            "chat": True,
            "coinflip": gamble_obj.coinflip.enabled,
            "commands": True,
            "cookie": commands_obj.cookie.enabled,
            "customcommands": self.settings_dict.customCommands.enabled,
            "daily": self.settings_dict.daily,
            "gems": self.settings_dict.autoUse.gems.enabled,
            "giveaway": self.settings_dict.giveaway.enabled,
            "hunt": commands_obj.hunt.enabled and not reaction_bot_obj.huntAndBattle,
            "huntbot": commands_obj.huntbot.enabled,
            "looper": should_start_looper,
            "lottery": commands_obj.lottery.enabled,
            "mail": self.settings_dict.mail,
            "others": True,
            "pupiku": commands_obj.pup.enabled
            or commands_obj.piku.enabled
            or commands_obj.run.enabled,
            "quest": self.settings_dict.autoQuest.enabled,
            "reactionbot": reactionbot,
            "sell": True,
            "shop": commands_obj.shop.enabled,
            "slots": gamble_obj.slots.enabled,
        }

    """To make the code cleaner when accessing cooldowns from config."""

    def random_float(self, cooldown_list):
        return self.random.uniform(cooldown_list[0], cooldown_list[1])

    async def sleep_till(self, cooldown, cd_list=True, noise=3):
        if cd_list:
            await asyncio.sleep(self.random_float(cooldown))
        else:
            await asyncio.sleep(self.random.uniform(cooldown, cooldown + noise))

    async def sleep(self, time):
        # to save imports
        await asyncio.sleep(time)

    async def log(
        self,
        text,
        color="#ffffff",
        bold=False,
        web_log=global_settings_dict.website.enabled,
        webhook_useless_log=global_settings_dict.webhook.logCommandSend,
        lineno=None,
        filename=None,
    ):
        current_time = datetime.now().strftime("%H:%M:%S")
        if self.misc["debug"]["enabled"]:
            if not lineno and not filename:
                frame_info = traceback.extract_stack()[-2]
                filename = os.path.basename(frame_info.filename)
                lineno = frame_info.lineno

            content_to_print = f"[#676585]❲{current_time}❳[/#676585] {self.username} - {text} | [#676585]❲{filename}:{lineno}❳[/#676585]"
            syst.system.console.print(content_to_print, style=color, markup=True)
            with lock:
                if self.misc["debug"]["logInTextFile"]:
                    with open("logs.txt", "a", encoding="utf-8") as log:
                        log.write(f"{content_to_print}\n")
        else:
            syst.system.console.print(
                f"{self.username}| {text}".center(syst.system.console_width - 2),
                style=color,
            )
        if web_log:
            with lock:
                website_append(
                    f"<div class='message'><span class='timestamp'>[{current_time}]</span><span class='text'>{self.username}| {text}</span></div>"
                )

        if webhook_useless_log:
            await self.send_webhook("on_command_send", command_send=text)

    async def fetch_slash_commands(self, channel):
        if self.slash_commands.get(str(channel.id)):
            return

        self.slash_commands[str(channel.id)] = []
        for command in await channel.application_commands():
            if command.application.id == self.owo_bot_id:
                self.slash_commands[str(channel.id)].append(command)

    async def send_webhook(
        self,
        data_id: str,
        username: str = "OwO-Dusk",
        webhook_url: str = None,
        pingid: str = None,
        **kwargs,
    ):
        """ "example_data": {
            "title": "",
            "description": "",
            "content": "",
            "color": "",
            "thumbnail": "",
            "author_name": "",
            "author_image": "",
            "footer": ""
        }"""

        data = webhook_data_dict.get(data_id, None)
        if not data:
            raise ValueError("Invalid data_id passed for fetching webhook embed data")
        data = data.copy()

        formattable_fields = [
            "title",
            "description",
            "content",
            "footer",
            "author_name",
            "thumbnail",
            "author_image",
        ]
        format_kwargs = {
            "username": self.user.name,
            "userid": self.user.id,
            "current_time": datetime.now().strftime("%H:%M:%S"),
            **kwargs,
        }
        for field in formattable_fields:
            if data.get(field):
                data[field] = data[field].format(**format_kwargs)

        color = data.get("color", None)
        if color:
            if isinstance(color, str) and color.startswith("#"):
                color = int(color.lstrip("#"), 16)
            else:
                color = int(color)
        else:
            color = 0x412280

        author_name = data.get("author_name", None)
        if not author_name and data.get("author_image"):
            author_name = "OwO-Dusk"

        embed = {
            "title": data.get("title", None),
            "description": data.get("description", None),
            "color": color,
            "footer": {"text": data.get("footer", None)},
            "thumbnail": {"url": data.get("thumbnail", None)},
            "author": {"name": author_name, "icon_url": data.get("author_image", None)},
        }

        content = data.get("content", "")
        if pingid:
            content += f"\n<@{pingid}>"

        payload = {
            "username": username,
            "embeds": [embed],
            "content": content,
        }

        async with self.webhook_lock:
            if not webhook_url:
                webhook_handler.send(payload)
            else:
                await webhook_handler.custom_send(payload, webhook_url)

    def calculate_correction_time(self, command):
        command = command.replace(" ", "")  # Remove spaces for accurate timing
        base_delay = self.random_float(self.settings_dict.misspell.baseDelay)
        rectification_time = sum(
            self.random_float(self.settings_dict.misspell.rectificationTime)
            for _ in command
        )
        total_time = base_delay + rectification_time
        return total_time

    # send commands
    async def send(
        self,
        message,
        color=None,
        bypass=False,
        channel=None,
        silent=global_settings_dict.silentMessage,
        typingIndicator=global_settings_dict.typingIndicator,
    ):
        """
        TASK: Refactor
        """

        if not channel:
            channel = self.cm
        disable_log = self.misc["console"]["disableCommandSendLog"]
        msg = message
        misspelled = False
        if self.settings_dict.misspell.enabled:
            misspelled = self.settings_dict.misspell.should_misspell()
            msg = misspell_word(message)
            # left off here!

        """
        TASK: remove repetition here
        """
        await self.wait_until_ready()
        if not self.ch.command_handler_status.captcha or bypass:
            if typingIndicator:
                async with channel.typing():
                    await channel.send(msg, silent=silent)
            else:
                await channel.send(msg, silent=silent)

            frame_info = traceback.extract_stack()[-2]
            filename = os.path.basename(frame_info.filename)
            lineno = frame_info.lineno
            if not disable_log:
                await self.log(
                    f"Ran: {msg}",
                    color if color else "#5432a8",
                    lineno=lineno,
                    filename=filename,
                )
            if misspelled:
                await self.ch.set_stat(False)
                time = self.calculate_correction_time(message)
                await self.log(
                    f"correcting: {msg} -> {message} in {time}s",
                    "#422052",
                    lineno=lineno,
                    filename=filename,
                )
                await asyncio.sleep(time)
                if typingIndicator:
                    async with channel.typing():
                        await channel.send(message, silent=silent)
                else:
                    await channel.send(message, silent=silent)
                await self.ch.set_stat(True)

    @suppress_and_log("Sending Slash Command")
    async def slashCommandSender(self, msg, color, channel, **kwargs):
        if not channel:
            channel = self.cm
        if not self.slash_commands.get(str(channel.id)):
            await self.fetch_slash_commands(channel)

        for command in self.slash_commands[str(channel.id)]:
            if command.name == msg:
                await self.wait_until_ready()
                await command(**kwargs)
                await self.log(f"Ran: /{msg}", color if color else "#5432a8")

    def calc_time(self):
        pst_timezone = pytz.timezone("US/Pacific")  # gets timezone
        current_time_pst = datetime.now(timezone.utc).astimezone(
            pst_timezone
        )  # current pst time
        midnight_pst = pst_timezone.localize(
            datetime(
                current_time_pst.year,
                current_time_pst.month,
                current_time_pst.day,
                0,
                0,
                0,
            )
        )  # gets 00:00 of the day
        time_until_12am_pst = (
            midnight_pst + timedelta(days=1) - current_time_pst
        )  # adds a day to the midnight to get time till next midnight, then subtract it with current time
        total_seconds = time_until_12am_pst.total_seconds()  # turn that time to seconds
        # 12am = 00:00, I might need this the next time I take a look here.
        return total_seconds

    # TBR
    def should_run(self, last_timestamp):
        # gets timezone
        pst = pytz.timezone("US/Pacific")

        now_pst = datetime.now(timezone.utc).astimezone(pst)  # current pst time
        last_pst = datetime.fromtimestamp(last_timestamp, timezone.utc).astimezone(pst)

        return now_pst.date() != last_pst.date()

    # TBR
    def time_in_seconds(self):
        """
        timestamp is basically seconds passed after 1970 jan 1st
        """
        time_now = datetime.now(timezone.utc).astimezone(pytz.timezone("US/Pacific"))
        return time_now.timestamp()

    # TBR
    def pst_midnight_timestamp(self):
        now = datetime.now(timezone.utc).astimezone(pytz.timezone("US/Pacific"))
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return midnight.timestamp()

    async def check_for_cash(self):
        await asyncio.sleep(self.random.uniform(4.5, 34.4))
        await self.ch.put_queue(
            {
                "cmd_name": self.alias["cash"]["normal"],
                "prefix": True,
                "checks": True,
                "id": "cash",
                "removed": False,
            }
        )

    def update_cash(self, amount, override=False, reduce=False, assumed=False):
        if override and self.settings_dict.cashCheck:
            self.stats.balance = amount
            self.stats.has_updated_balance = True
        else:
            if self.settings_dict.cashCheck and not assumed:
                if reduce:
                    self.stats.balance -= amount
                else:
                    self.stats.balance += amount

            if reduce:
                self.stats.net_earnings -= amount
            else:
                self.stats.net_earnings += amount
        self.db.update_cash_db()

    def get_nick(self, msg):
        if not msg.guild:
            return ""
        else:
            user = msg.guild.me
            if user.nick:
                return user.nick
            elif user.display_name:
                return user.display_name
            else:
                return user.name

    async def setup_hook(self):
        # Randomise user
        self.lock = asyncio.Lock()
        self.webhook_lock = asyncio.Lock()
        if self.misc["debug"]["hideUser"]:
            x = [
                "Sunny",
                "River",
                "Echo",
                "Sky",
                "Shadow",
                "Nova",
                "Jelly",
                "Pixel",
                "Cloud",
                "Mint",
                "Flare",
                "Breeze",
                "Dusty",
                "Blip",
            ]
            random_part = self.random.choice(x)
            self.username = (
                f"{random_part}_{abs(hash(str(self.user.id) + random_part)) % 10000}"
            )
        else:
            self.username = self.user.name

        self.safety_check_loop.start()
        self.local_headers = await components.headers.generate_headers()
        self.local_headers["Authorization"] = self.token
        if self.session is None:
            self.session = aiohttp.ClientSession()

        self.quest_handler = LocalQuestHandler(
            global_quest_handler, self.user.id, self.session
        )

        syst.system.print_box(
            f"-Loaded {self.username}[*].".center(syst.system.console_width - 2),
            "bold royal_blue1 ",
        )
        list_user_ids.append(self.user.id)

        await self.db.update_priorities()

        # Fetch the channel
        self.cm = self.get_channel(self.channel_id)

        if not self.cm:
            try:
                self.cm = await self.fetch_channel(self.channel_id)
            except discord.NotFound:
                await self.log(
                    f"Error - Channel with ID {self.channel_id} does not exist.",
                    "#c25560",
                )
                return
            except discord.Forbidden:
                await self.log(
                    f"Bot lacks permissions to access channel {self.channel_id}.",
                    "#c25560",
                )
                return
            except discord.HTTPException as e:
                await self.log(
                    f"Failed to fetch channel {self.channel_id}: {e}", "#c25560"
                )
                return

        self.cm_slowmode_cd = self.cm.slowmode_delay

        # self.nick_name = self.cm.guild.me.nick

        # self.dm = await (await self.fetch_user(self.owo_bot_id)).create_dm()
        # remove temp fix in `cogs/captcha.py` if uncommenting

        # Stores slash commands. This will be populated.
        self.slash_commands = {}

        await self.fetch_slash_commands(self.cm)

        # Charts
        await self.db.populate_stats_db()

        await self.db.populate_cowoncy_earnings()
        await self.db.reset_gamble_wins_or_losses()

        await self.db.fetch_net_earnings()

        # Start various tasks and updates
        # self.config_update_checker.start()
        # disabled since unnecessory
        if self.token_len > 1:
            time_to_sleep = self.random_float(global_settings_dict.account.startupDelay)
            await self.log(f"{self.username} sleeping {time_to_sleep}s before starting")
            await asyncio.sleep(time_to_sleep)

        await self.update_config()

        if self.global_settings_dict.offlineStatus:
            self.presence.start()

        if self.settings_dict.sleep.enabled:
            self.random_sleep.start()

        if self.settings_dict.cashCheck:
            asyncio.create_task(self.check_for_cash())
