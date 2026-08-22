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

# Most errors should be caught by frontend. Just rough checks.
# I like things named this way in code. So might be named entirely differently
# in the code compared to the settings.json file.


"""
Task :
Consider actually erroring instead of defaulting to values for non-cooldown parts
Also confirm all settings are updating.

also ensure types aren't none, and values actually exist
"""

from utils.config_models import validators
from utils.config_models.helpers import expected_fetch


class GlobalSettings:
    def __init__(self, d: dict):
        self.typingIndicator = expected_fetch(d, "typingIndicator", bool)
        self.silentMessage = expected_fetch(d, "silentMessages", bool)
        self.offlineStatus = expected_fetch(d, "offlineStatus", bool)
        self.ocrApi = expected_fetch(d, "ocrApi", str)

        # Website Dashboard
        self.website = Website(expected_fetch(d, "website", dict))

        # Database
        self.database = Database(expected_fetch(d, "database", dict))

        # Account Delays
        self.account = Account(expected_fetch(d, "account", dict))

        # Text Commands
        self.textCommands = TextCommands(expected_fetch(d, "textCommands", dict))

        # Webhook Logging
        self.webhook = Webhook(expected_fetch(d, "webhook", dict))

        # Console commands
        self.console = Console(expected_fetch(d, "console", dict))

        # Captcha
        self.captcha = Captcha(expected_fetch(d, "captcha", dict))

        # Battery Check
        self.batteryCheck = BatteryCheck(expected_fetch(d, "batteryCheck", dict))

        # Channel Switcher
        self.channelSwitcher = ChannelSwitcher(
            expected_fetch(d, "channelSwitcher", dict)
        )


class Website:
    def __init__(self, d: dict):
        self.enabled = expected_fetch(d, "enabled", bool)
        self.port = expected_fetch(d, "port", int)
        self.refreshInterval = expected_fetch(d, "refreshInterval", int)
        self.password = expected_fetch(d, "password", str)
        self.enableHost = expected_fetch(d, "enableHost", bool)


class Database:
    def __init__(self, d: dict):
        self.logStatistics = expected_fetch(d, "logStatistics", bool)


class Account:
    def __init__(self, d: dict):
        self.startupDelay = expected_fetch(d, "startupDelay", list, float)
        self.commandsStart = expected_fetch(d, "commandsStartDelay", list, float)
        self.commandsHandlerStart = expected_fetch(
            d, "commandsHandlerStartDelay", list, float
        )

        # Ensures all cooldowns are valid:
        # May want to consider namings in global_settings.json file.
        validators.validate_cooldown(self.startupDelay)
        validators.validate_cooldown(self.commandsStart)
        validators.validate_cooldown(self.commandsHandlerStart)


class TextCommands:
    def __init__(self, d: dict):
        self.prefix = expected_fetch(d, "prefix", str)
        self.stopCommand = expected_fetch(d, "commandToStopUser", str)
        self.startCommand = expected_fetch(d, "commandToStartUser", str)
        self.restartCommand = expected_fetch(d, "commandToRestartAfterCaptcha", str)
        self.switchChannelCommand = expected_fetch(d, "CommandToSwitchChannel", str)
        self.sleepCommand = expected_fetch(d, "commandToSleep", str)
        self.defaultSleepDuration = expected_fetch(d, "defaultSleepDuration", int)
        self.allowedUsers = expected_fetch(d, "allowedUsers", list, int)


class Webhook:
    def __init__(self, d: dict):
        self.enabled = expected_fetch(d, "enabled", bool)
        self.logCommandSend = expected_fetch(d, "logCommandSend", bool)
        self.webhookUrl = d.get("webhookUrl") or ""
        self.webhookCaptchaUrl = d.get("webhookCaptchaUrl") or ""
        self.pingUserId = d.get("webhookUserIdToPingOnCaptcha") or ""

        self.animalLog = AnimalLog(expected_fetch(d, "animalLog", dict))

        self.others = WebhookOthers(expected_fetch(d, "others", dict))


class AnimalLog:
    # Part of `Webhook` class
    def __init__(self, d: dict):
        self.enabled = expected_fetch(d, "enabled", bool)
        self.rank = AnimalLogRank(expected_fetch(d, "rank", dict))


class AnimalLogRank:
    # Part of `AnimalLog` class, defines what all animals can be logged.
    def __init__(self, d: dict):
        self._rank = [
            "common",
            "uncommon",
            "rare",
            "epic",
            "mythical",
            "gem",
            "legendary",
            "fabled",
            "hidden",
            "distorted",
        ]

        for rank in self._rank:
            setattr(self, rank, expected_fetch(d, rank, bool))


class WebhookOthers:
    # Part of `Webhook` class
    def __init__(self, d: dict):
        self.lootbox = expected_fetch(d, "logLootbox", bool)
        self.crate = expected_fetch(d, "logCrate", bool)
        self.logChannelSwitch = expected_fetch(d, "logChannelSwitch", bool)


class Console:
    # Console commands on captcha.
    def __init__(self, d: dict):
        self.onCaptcha = expected_fetch(d, "runConsoleCommandOnCaptcha", bool)
        self.onBan = expected_fetch(d, "runConsoleCommandOnBan", bool)

        self.captchaCommand = expected_fetch(d, "commandToRunOnCaptcha", str)
        self.banCommand = expected_fetch(d, "commandToRunOnBan", str)


class Captcha:
    def __init__(self, d: dict):
        self.openCaptchaWebsite = expected_fetch(d, "openCaptchaWebsite", bool)
        self.stopIfFailure = expected_fetch(d, "stopCodeIfFailedToSolve", bool)

        # Notifications
        self.notifications = Notifications(expected_fetch(d, "notifications", dict))

        # Play Audio
        self.playAudio = PlayAudio(expected_fetch(d, "playAudio", dict))

        # Toast and Popup
        self.toastOrPopup = ToastOrPopup(expected_fetch(d, "toastOrPopup", dict))

        # Termux specific
        self.termux = Termux(expected_fetch(d, "termux", dict))


class Notifications:
    # Part of `Captcha` class
    def __init__(self, d: dict):
        self.enabled = expected_fetch(d, "enabled", bool)
        self.captchaContent = expected_fetch(d, "captchaContent", str)
        self.bannedContent = expected_fetch(d, "bannedContent", str)

        self.reccur = Reccur(expected_fetch(d, "reccur", dict))


class Reccur:
    def __init__(self, d: dict):
        self.enabled = expected_fetch(d, "enabled", bool)
        self.timesToReccur = expected_fetch(d, "timesToReccur", int)


class PlayAudio:
    # Part of `Captcha` class
    def __init__(self, d: dict):
        self.enabled = expected_fetch(d, "enabled", bool)
        self.path = expected_fetch(d, "path", str)


class ToastOrPopup:
    def __init__(self, d: dict):
        self.enabled = expected_fetch(d, "enabled", bool)
        self.captchaContent = expected_fetch(d, "captchaContent", str)
        self.bannedContent = expected_fetch(d, "bannedContent", str)
        self.termuxToast = TermuxToast(expected_fetch(d, "termuxToast", dict))


class TermuxToast:
    def __init__(self, d: dict):
        self.backgroundColour = expected_fetch(d, "backgroundColour", str)
        self.textColour = expected_fetch(d, "textColour", str)
        self.position = expected_fetch(d, "position", str)


class Termux:
    # Part of `Captcha` class
    # Termux only part
    def __init__(self, d: dict):
        self.vibrate = Vibrate(expected_fetch(d, "vibrate", dict))
        self.textToSpeech = TextToSpeech(expected_fetch(d, "textToSpeech", dict))


class Vibrate:
    def __init__(self, d: dict):
        self.enabled = expected_fetch(d, "enabled", bool)
        self.time = expected_fetch(d, "time", int)


class TextToSpeech:
    def __init__(self, d: dict):
        self.enabled = expected_fetch(d, "enabled", bool)
        self.captchaContent = expected_fetch(d, "captchaContent", str)
        self.bannedContent = expected_fetch(d, "bannedContent", str)


class BatteryCheck:
    def __init__(self, d: dict):
        self.enabled = expected_fetch(d, "enabled", bool)
        self.minPercentage = expected_fetch(d, "minPercentage", int)
        self.refreshInterval = expected_fetch(d, "refreshInterval", int)

        validators.validate_frequency(self.minPercentage)


class ChannelSwitcher:
    def __init__(self, d: dict):
        self.enabled = expected_fetch(d, "enabled", bool)

        self.allUsers = expected_fetch(
            expected_fetch(d, "allUsers", dict), "channels", list, int
        )
        self.users = []
        for user_dict in expected_fetch(d, "users", list, dict):
            self.users.append(User(user_dict))

        self.interval = expected_fetch(d, "interval", list, float)
        self.delayBeforeSwitch = expected_fetch(d, "delayBeforeSwitch", list, float)

        validators.validate_cooldown(self.interval)
        validators.validate_cooldown(self.delayBeforeSwitch)


class User:
    def __init__(self, d: dict):
        self.userid = expected_fetch(d, "userid", int)
        self.channels = expected_fetch(d, "channels", list, int)
