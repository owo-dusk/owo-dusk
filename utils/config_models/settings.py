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

import random

from utils.config_models import validators
from utils.config_models.helpers import expected_fetch


def get_cd(cd: list):
    validators.validate_cooldown(cd)
    return random.uniform(cd[0], cd[1])


class Settings:
    def __init__(self, d: dict):
        self.useSlashCommands = expected_fetch(d, "useSlashCommands", bool)
        self.daily = expected_fetch(d, "autoDaily", bool)
        self.cashCheck = expected_fetch(d, "cashCheck", bool)
        self.prefix = expected_fetch(d, "setprefix", str)
        self.mail = expected_fetch(d, "claimMail", bool)

        # Commands
        self.commands = Commands(expected_fetch(d, "commands", dict))

        # Gambling
        self.gamble = Gambling(expected_fetch(d, "gamble", dict))

        # Boss battles
        self.boss = BossBattle(expected_fetch(d, "bossBattle", dict))

        # Giveaways
        self.giveaway = Giveaway(expected_fetch(d, "giveawayJoiner", dict))

        # sleeping
        self.sleep = Sleep(expected_fetch(d, "sleep", dict))

        # misspell
        self.misspell = Misspell(expected_fetch(d, "misspell", dict))

        # Cooldowns
        self.cooldowns = Cooldowns(expected_fetch(d, "defaultCooldowns", dict))

        # Auto Use
        self.autoUse = AutoUse(expected_fetch(d, "autoUse", dict))

        # Custom command
        self.customCommands = CustomCommands(expected_fetch(d, "customCommands", dict))

        # Auto sell/sac - Animal
        self.animal = Animal(expected_fetch(d, "animal", dict))

        # Auto Quest
        self.autoQuest = AutoQuest(expected_fetch(d, "autoQuest", dict))


GEMS_RARITY = [
    "common",
    "uncommon",
    "rare",
    "epic",
    "mythical",
    "legendary",
    "fabled",
]


def find_least_gap(list_to_check):
    if len(list_to_check) < 2:
        return None

    final_result = {
        "min": list_to_check[0],
        "max": list_to_check[1],
        "diff": abs(list_to_check[1] - list_to_check[0]),
    }

    for i in range(len(list_to_check) - 1):
        curr = list_to_check[i]
        next_item = list_to_check[i + 1]
        diff = abs(next_item - curr)

        if diff < final_result["diff"]:
            final_result["min"] = curr
            final_result["max"] = next_item
            final_result["diff"] = diff if diff > 0 else 1

    return final_result


class AutoQuest:
    def __init__(self, d: dict):
        self.enabled = expected_fetch(d, "enabled", bool)

        helpChannel = expected_fetch(d, "helpChannel", dict)
        self.useHelpChannel = expected_fetch(helpChannel, "postInHelpChannel", bool)
        self.channelId = expected_fetch(helpChannel, "channelId", int)

        self.helpOthers = expected_fetch(d, "helpOthers", bool)
        self.canEnable = expected_fetch(d, "enableCommandsToCompleteQuest", bool)
        self.checkCooldown = expected_fetch(d, "checkCooldown", list, float)

    def get_cd(self):
        return get_cd(self.checkCooldown)


class CustomCommands:
    def __init__(self, d: dict):
        self.enabled = expected_fetch(d, "enabled", bool)
        self.commands = []
        for item in expected_fetch(d, "commands", list):
            self.commands.append(CustomCommand(item))

    def approximate_minimum_cooldown(self):
        # There seems to be some logical issues here
        # may need to double check.
        cooldowns_list = [item.cooldown for item in self.commands if item.enabled]

        if not cooldowns_list:
            # just in case
            return 1

        # Sort in ascending order
        cooldowns_list = sorted(cooldowns_list)
        result = find_least_gap(cooldowns_list)

        if result:
            return min(result["diff"], cooldowns_list[0])
        else:
            return cooldowns_list[0]


class CustomCommand:
    """
    Item of `CustomCommands`
    """

    def __init__(self, d: dict):
        self.enabled = d.get("enabled", False)
        self.command = d.get("command", "")
        self.cooldown = d.get("cooldown", 0)

        if self.cooldown <= 0:
            raise ValueError("Don't use 0 as cooldown.")


class AutoUse:
    def __init__(self, d: dict):
        self.lootbox = expected_fetch(d, "autoLootbox", bool)
        self.crate = expected_fetch(d, "autoCrate", bool)
        self.gems = Gems(expected_fetch(d, "gems", dict))


class Gems:
    def __init__(self, d: dict):
        # Task: Re check implementation if required.
        self.enabled = expected_fetch(d, "enabled", bool)
        self.tiers = expected_fetch(d, "tiers", dict)
        self.gemsToUse = expected_fetch(d, "gemsToUse", dict)
        self.disableHuntIfNoGems = expected_fetch(d, "disableHuntIfNoGems", bool)
        self.dynamicSpecialGem = expected_fetch(d, "dynamicSpecialGemUsage", bool)

        order = expected_fetch(d, "order", dict)
        self.useLowest = expected_fetch(order, "lowestToHighest", bool)


class Cooldowns:
    def __init__(self, d: dict):
        # Assuming cooldown timers are integers/numbers
        self.longCooldown = expected_fetch(d, "longCooldown", list, float)
        self.moderateCooldown = expected_fetch(d, "moderateCooldown", list, float)
        self.shortCooldown = expected_fetch(d, "shortCooldown", list, float)
        self.briefCooldown = expected_fetch(d, "briefCooldown", list, float)
        self.captchaRestart = expected_fetch(d, "captchaRestart", list, float)
        self.commandHandler = CommandHandler(expected_fetch(d, "commandHandler", dict))
        # Reaction Bot
        self.reactionBot = ReactionBot(expected_fetch(d, "reactionBot", dict))


class CommandHandler:
    def __init__(self, d: dict):
        self.betweenCommands = expected_fetch(d, "betweenCommands", list, float)
        self.readdingToQueue = expected_fetch(d, "beforeReaddingToQueue", float)


class ReactionBot:
    def __init__(self, d: dict):
        self.huntAndBattle = expected_fetch(d, "huntAndBattle", bool)
        self.owo = expected_fetch(d, "owo", bool)
        self.prayAndCurse = expected_fetch(d, "prayAndCurse", bool)
        self.cooldown = expected_fetch(d, "cooldown", list, float)

    def get_cd(self):
        return get_cd(self.cooldown)


class Misspell:
    def __init__(self, d: dict):
        self.enabled = expected_fetch(d, "enabled", bool)
        self.frequency = expected_fetch(d, "frequencyPercentage", int)
        self.baseDelay = expected_fetch(d, "baseDelay", list, float)
        self.rectificationTime = expected_fetch(
            d, "errorRectificationTimePerLetter", list, float
        )

        validators.validate_frequency(self.frequency)

    def should_misspell(self):
        random_num = random.randint(1, 100)
        return random_num > (100 - self.frequency)


class Sleep:
    def __init__(self, d: dict):
        self.enabled = expected_fetch(d, "enabled", bool)
        self.frequency = expected_fetch(d, "frequencyPercentage", int)
        self.checkTime = expected_fetch(d, "checkTime", list, float)
        self.sleeptime = expected_fetch(d, "sleepTime", list, float)

        validators.validate_frequency(self.frequency)

    def should_sleep(self):
        random_num = random.randint(1, 100)
        return random_num > (100 - self.frequency)

    def get_sleep_time(self):
        if self.sleeptime:
            if self.sleeptime[0] > self.sleeptime[1]:
                raise ValueError("Max cooldown must be greater than min.")

            if self.sleeptime[0] == self.sleeptime[1]:
                raise ValueError("Both min and max cooldown same..")

            return random.uniform(self.sleeptime[0], self.sleeptime[1])
        else:
            raise ValueError("No cooldown?")

    def get_check_time(self):
        if self.checkTime:
            if self.checkTime[0] > self.checkTime[1]:
                raise ValueError("Max cooldown must be greater than min.")

            if self.checkTime[0] == self.checkTime[1]:
                raise ValueError("Both min and max cooldown same..")

            return random.uniform(self.checkTime[0], self.checkTime[1])
        else:
            raise ValueError("No valid checktime available")


class Giveaway:
    def __init__(self, d: dict):
        self.enabled = expected_fetch(d, "enabled", bool)
        self.messageRangeToCheck = expected_fetch(d, "messageRangeToCheck", int)
        self.cooldown = expected_fetch(d, "cooldown", list, float)
        self.channels = expected_fetch(d, "channelsToJoin", list, int)

    def get_cd(self):
        return get_cd(self.cooldown)


class BossBattle:
    def __init__(self, d: dict):
        self.enabled = expected_fetch(d, "enabled", bool)
        self.joinChance = expected_fetch(d, "joinChancePercent", int)
        self.joinAll = expected_fetch(d, "joinAllGuilds", bool)

        if not 0 <= self.joinChance <= 100:
            raise ValueError("Invalid join percent: must be between 0 and 100")

        rules = d.get("guildJoinRules", {})
        self.joinGuilds = rules.get("onlyJoinGuildIds", [])
        self.ignoreGuilds = rules.get("ignoreGuildIds", [])

    def should_join(self):
        random_num = random.randint(1, 100)
        return random_num > (100 - self.joinChance)


class Gambling:
    def __init__(self, d: dict):
        self.allottedAmount = expected_fetch(d, "allottedAmount", int)
        self.goals = GamblingGoals(expected_fetch(d, "goalSystem", dict))

        for cmd in ["coinflip", "slots", "blackjack"]:
            setattr(self, cmd, GambleItem(expected_fetch(d, cmd, dict)))


class GamblingGoals:
    def __init__(self, d: dict):
        self.enabled = expected_fetch(d, "enabled", bool)
        self.amount = expected_fetch(d, "amount", int)


class GambleItem:
    def __init__(self, d: dict):
        self.enabled = expected_fetch(d, "enabled", bool)
        self.startValue = expected_fetch(d, "startValue", int)
        self.multiplier = expected_fetch(d, "multiplierOnLose", int)
        self.cooldown = expected_fetch(d, "cooldown", list, float)

        cf_options = d.get("options", None)
        if cf_options:
            self.options = CoinflipOptions(cf_options)

    def get_cd(self):
        return get_cd(self.cooldown)


class CoinflipOptions:
    def __init__(self, d: dict):
        self.heads = expected_fetch(d, "heads", bool)
        self.tails = expected_fetch(d, "tails", bool)

    def random_choice(self):
        choices = []
        if self.heads:
            choices.append("h")
        if self.tails:
            choices.append("t")
        return random.choice(choices or ["h"])


class Commands:
    """Contains -> hunt, battle, sell, sac, pray, curse, lvlGrind, cookie, oow, shop, huntbot, lottery, army, pup, piku
    each with `get_cd` function"""

    def __init__(self, d: dict):
        cmd_list = [
            "hunt",
            "battle",
            "pray",
            "curse",
            "lvlGrind",
            "cookie",
            "owo",
            "army",
            "pup",
            "piku",
            "run",
        ]
        for cmd in cmd_list:
            setattr(self, cmd, Command(expected_fetch(d, cmd, dict)))

        self.shop = ShopCommand(expected_fetch(d, "shop", dict))
        self.huntbot = HuntbotCommand(expected_fetch(d, "autoHuntBot", dict))
        self.lottery = Lottery(expected_fetch(d, "lottery", dict))


class Command:
    def __init__(self, d: dict):
        self.enabled = expected_fetch(d, "enabled", bool)
        self.cooldown = d.get("cooldown", [])

        # Hunt and Battle
        self.shortform = d.get("useShortForm", None)
        # Hunt only
        self.show_streak = d.get("showStreakInConsole", None)
        self.notify_streak_loss = d.get("notifyStreakLoss", None)

        # Pray and Curse has user id as list while cookie uses int
        # Might need to cleanly handle this later.
        self.user_id = d.get("userid", None)
        self.ping_user = d.get("pingUser", False)
        if d.get("customChannel"):
            self.custom_channel = CustomChannel(d.get("customChannel"))
        self.count = d.get("count", False)

        # level grind
        self.useQuote = d.get("useQuoteInstead", None)
        self.minLength = d.get("minLengthForRandomString", None)
        self.maxLength = d.get("maxLengthForRandomString", None)

        # OwO only
        self.prioritise = d.get("prioritise", False)

    def get_cd(self):
        return get_cd(self.cooldown)


class Lottery:
    def __init__(self, d: dict):
        self.enabled = expected_fetch(d, "enabled", bool)
        self.amount = expected_fetch(d, "amount", int)


class Animal:
    def __init__(self, d: dict):
        self.sell = AnimalSellSac(expected_fetch(d, "sell", dict))
        self.sac = AnimalSellSac(expected_fetch(d, "sac", dict))
        self.cooldown = expected_fetch(d, "cooldown", list, float)

    def get_cd(self):
        return get_cd(self.cooldown)


class AnimalSellSac:
    def __init__(self, d: dict):
        self.enabled = expected_fetch(d, "enabled", bool)
        self.rarity = Rarity(expected_fetch(d, "rarity", dict))


class Rarity:
    """
    Sell and Sacrifice rarities. Also has a function `get_rarities` to get rarities as a string.
    """

    def __init__(self, d: dict):
        self._rarities = [
            "common",
            "uncommon",
            "rare",
            "epic",
            "special",
            "mythical",
            "gem",
            "legendary",
            "fabled",
            "hidden",
            "distorted",
        ]
        for rarity in self._rarities:
            setattr(self, rarity, d.get(rarity, False))

    def get_rarities(self):
        # Get first letter of all enabled rarity joined with space as a string
        rarities = ""
        for rarity in self._rarities:
            if getattr(self, rarity):
                rarities += f"{rarity[0]} "
        return rarities.strip()


RING_PRICES = [
    ("common", 10),
    ("uncommon", 100),
    ("rare", 1000),
    ("epic", 10000),
    ("mythical", 100000),
    ("legendary", 1000000),
    ("fabled", 10000000),
]


class ShopCommand:
    def __init__(self, d: dict):
        self.enabled = expected_fetch(d, "enabled", bool)
        self.cooldown = expected_fetch(d, "cooldown", list, float)
        self.items = ShopItems(expected_fetch(d, "itemsToBuy", dict))

    def get_cd(self):
        return get_cd(self.cooldown)

    def get_price_and_id(self, ring):
        for idx, (name, price) in enumerate(RING_PRICES, start=1):
            if name == ring:
                return price, idx
        return 0, 0

    def get_items_to_buy(self, cur_cash, cash_check=True):
        items_to_buy = []
        for ring, _ in RING_PRICES:
            if getattr(self.items, ring, False):
                price, item_id = self.get_price_and_id(ring)
                if cur_cash >= price or not cash_check:
                    items_to_buy.append(item_id)
        return items_to_buy


class ShopItems:
    """
    Contains shop items for `shop` command
    """

    def __init__(self, d: dict):
        for ring, _ in RING_PRICES:
            # self.common etc. named commonRing in settings.
            setattr(self, ring, expected_fetch(d, f"{ring}Ring", bool))


class CustomChannel:
    """
    For Pray and Curse custom channel
    """

    def __init__(self, d: dict):
        self.enabled = expected_fetch(d, "enabled", bool)
        self.channel = expected_fetch(d, "channelId", int)


class HuntbotCommand:
    def __init__(self, d: dict):
        self.enabled = expected_fetch(d, "enabled", bool)
        self.cashToSpend = expected_fetch(d, "cashToSpend", int)
        self.upgrader = HuntbotUpgrader(expected_fetch(d, "upgrader", dict))


HUNTBOT_TRAITS = [
    "efficiency",
    "duration",
    "cost",
    "gain",
    "exp",
    "radar",
]


class HuntbotUpgrader:
    def __init__(self, d: dict):
        self.enabled = expected_fetch(d, "enabled", bool)
        self.sleeptime = expected_fetch(d, "sleeptime", list, float)
        self.traits = HuntbotTraits(expected_fetch(d, "traits", dict))
        self.weights = HuntbotWeights(expected_fetch(d, "weights", dict))

    def get_cd(self):
        return get_cd(self.sleeptime)

    def get_enabled_traits(self):
        enabled_traits = []
        for trait in HUNTBOT_TRAITS:
            if getattr(self.traits, trait):
                enabled_traits.append(trait)
        return enabled_traits


class HuntbotTraits:
    def __init__(self, d: dict):
        for trait in HUNTBOT_TRAITS:
            setattr(self, trait, expected_fetch(d, trait, bool))


class HuntbotWeights:
    def __init__(self, d: dict):
        for trait in HUNTBOT_TRAITS:
            setattr(self, trait, expected_fetch(d, trait, int))
