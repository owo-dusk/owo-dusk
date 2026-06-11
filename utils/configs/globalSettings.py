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

from utils.configs import validators


class GlobalSettings:
    def __init__(self, d: dict):
        self.typingIndicator = d.get("typingIndicator", False)
        self.silentMessage = d.get("silentMessages", False)  # Changed
        self.offlineStatus = d.get("offlineStatus", False)
        self.ocrApi = d.get("ocrApi", "helloworld")

        # Website Dashboard
        self.website = Website(d.get("website", {}))

        # Account Delays
        self.account = Account(d.get("account", {}))

        # Text Commands
        self.textCommands = TextCommands(d.get("textCommands", {}))

        # Webhook Logging
        self.webhook = Webhook(d.get("webhook", {}))

        # Console commands
        self.console = Console(d.get("console", {}))

        # Captcha
        self.captcha = Captcha(d.get("captcha", {}))

        # Battery Check
        self.batteryCheck = BatteryCheck(d.get("batteryCheck", {}))

        # Channel Switcher
        self.channelSwitcher = ChannelSwitcher(d.get("channelSwitcher", {}))


class Website:
    def __init__(self, d: dict):
        self.enabled = d.get("enabled", False)
        self.port = d.get("port", 1200)
        self.refreshInterval = d.get("refreshInterval", 15)
        self.password = d.get("password", "areallylongandsecretpassword")
        self.enableHost = d.get("enableHost", False)


class Account:
    def __init__(self, d: dict):
        self.startupDelay = d.get("startupDelay", [])
        self.commandsStart = d.get("commandsStartDelay", [])  # Changed
        self.commandsHandlerStart = d.get("commandsHandlerStartDelay", [])  # Changed

        # Ensures all cooldowns are valid:
        # May want to consider namings in global_settings.json file.
        validators.validateCooldown(self.startupDelay)
        validators.validateCooldown(self.commandsStart)
        validators.validateCooldown(self.commandsHandlerStart)


class TextCommands:
    def __init__(self, d: dict):
        self.prefix = d.get("prefix", ".")
        self.stopCommand = d.get("commandToStopUser", "stop")  # Changed
        self.startCommand = d.get("commandToStartUser", "start")  # Changed
        self.restartCommand = d.get(
            "commandToRestartAfterCaptcha", "restart_captcha"
        )  # Changed
        self.switchChannelCommand = d.get("CommandToSwitchChannel", "switch_channel")
        self.sleepCommand = d.get("commandToSleep", "sleep")
        self.defaultSleepDuration = d.get("defaultSleepDuration", 600)
        self.allowedUsers = d.get("allowedUsers", [])


class Webhook:
    def __init__(self, d: dict):
        self.enabled = d.get("enabled", False)
        self.logCommandSend = d.get("logCommandSend", False)
        self.webhookUrl = d.get("webhookUrl") or ""
        self.webhookCaptchaUrl = d.get("webhookCaptchaUrl") or ""
        self.pingUserId = d.get("webhookUserIdToPingOnCaptcha") or ""  # changed

        self.animalLog = AnimalLog(d.get("animalLog", {}))  # Changed + json changed

        self.others = WebhookOthers(d.get("others", {}))


class AnimalLog:
    # Part of `Webhook` class
    def __init__(self, d: dict):
        self.enabled = d.get("enabled", False)
        self.rank = AnimalLogRank(d.get("rank", {}))


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
            setattr(self, rank, d.get(rank, False))


class WebhookOthers:
    # Part of `Webhook` class
    def __init__(self, d: dict):
        self.lootbox = d.get("logLootbox")  # Changed
        self.crate = d.get("logCrate")  # Changed
        self.logChannelSwitch = d.get("logChannelSwitch", False)


class Console:
    # Console commands on captcha.
    def __init__(self, d: dict):
        self.onCaptcha = d.get("runConsoleCommandOnCaptcha", False)  # Changed
        self.onBan = d.get("runConsoleCommandOnBan", None)  # Changed

        self.captchaCommand = d.get("commandToRunOnCaptcha", "")  # Changed
        self.banCommand = d.get("commandToRunOnBan", "")  # Changed


class Captcha:
    def __init__(self, d: dict):
        self.openCaptchaWebsite = d.get("openCaptchaWebsite", False)
        self.stopIfFailure = d.get("stopCodeIfFailedToSolve", False)  # Changed
        # Notifications
        self.notifications = Notifications(d.get("notifications", {}))
        # Play Audio
        self.playAudio = PlayAudio(d.get("playAudio", {}))
        # Toast and Popup
        self.toastOrPopup = ToastOrPopup(d.get("toastOrPopup", {}))
        # Termux specific
        self.termux = Termux(d.get("termux", {}))


class Notifications:
    # Part of `Captcha` class
    def __init__(self, d: dict):
        self.enabled = d.get("enabled", False)
        self.captchaContent = d.get("captchaContent", "captcha content missing")
        self.bannedContent = d.get("bannedContent", "banned content missing")

        self.reccur = Reccur(d.get("reccur", {}))


class Reccur:
    def __init__(self, d: dict):
        self.enabled = d.get("enabled", False)
        self.timesToReccur = d.get("timesToReccur", 3)  # Changed - JSON


class PlayAudio:
    # Part of `Captcha` class
    def __init__(self, d: dict):
        self.enabled = d.get("enabled", False)
        self.path = d.get("path", "")


class ToastOrPopup:
    def __init__(self, d: dict):
        self.enabled = d.get("enabled", False)
        self.captchaContent = d.get("captchaContent", "captcha content missing")
        self.bannedContent = d.get("bannedContent", "banned content missing")
        # Termux customization
        self.termuxToast = TermuxToast(d.get("termuxToast", {}))


class TermuxToast:
    def __init__(self, d: dict):
        self.backgroundColour = d.get("backgroundColour", "black")
        self.textColour = d.get("textColour", "red")
        self.position = d.get("position", "middle")


class Termux:
    # Part of `Captcha` class
    # Termux only part
    def __init__(self, d: dict):
        self.vibrate = Vibrate(d.get("vibrate", {}))
        self.textToSpeech = TextToSpeech(d.get("textToSpeech", {}))


class Vibrate:
    def __init__(self, d: dict):
        self.enabled = d.get("enabled", False)
        self.time = d.get("time", 5)


class TextToSpeech:
    def __init__(self, d: dict):
        self.enabled = d.get("enabled", False)
        self.captchaContent = d.get("captchaContent", "captcha content missing")
        self.bannedContent = d.get("bannedContent", "banned content missing")


class BatteryCheck:
    def __init__(self, d: dict):
        self.enabled = d.get("enabled", False)
        self.minPercentage = d.get("minPercentage")
        self.refreshInterval = d.get("refreshInterval")

        validators.validateFrequency(self.minPercentage)


class ChannelSwitcher:
    def __init__(self, d: dict):
        self.enabled = d.get("enabled", False)

        self.allUsers = d.get("allUsers", {}).get("channels", [])  # Changed
        self.users = []
        for user_dict in d.get("users", []):
            self.users.append(User(user_dict))
        self.interval = d.get("interval", [])
        self.delayBeforeSwitch = d.get("delayBeforeSwitch", [])

        validators.validateCooldown(self.interval)
        validators.validateCooldown(self.delayBeforeSwitch)


class User:
    def __init__(self, d: dict):
        self.userid = d.get("userid")
        self.channels = d.get("channels", [])
