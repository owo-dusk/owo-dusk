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


class Settings:
    def __init__(self, d: dict):
        self.useSlashCommands = d.get("useSlashCommands", False)
        self.daily = d.get("autoDaily", False)
        self.cashCheck = d.get("cashCheck", False)
        self.prefix = d.get("setprefix", "owo ")

        # Commands
        self.commands = Commands(d.get("commands", {}))

        # Gambling
        self.gamble = Gambling(d.get("gamble", {}))

        # Boss battles
        self.boss = BossBattle(d.get("bossBattle", {}))

        # Giveaways
        self.giveaway = Giveaway(d.get("giveawayJoiner", {}))

        # sleeping
        self.sleep = Sleep(d.get("sleep", {}))

        # misspell
        self.misspell = Misspell(d.get("misspell", {}))

        # Cooldowns
        self.cooldowns = Cooldowns(d.get("defaultCooldowns", {}))

        # Auto Use
        self.autoUse = AutoUse(d.get("autoUse", {}))

        # Custom command
        self.customCommands = CustomCommands(d.get("customCommands", {}))


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


class CustomCommands:
    def __init__(self, d: dict):
        self.enabled = d.get("enabled", False)
        self.commands = []
        for item in d.get("commands", []):
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
        self.lootbox = d.get("autoLootbox", False)
        self.crate = d.get("autoCrate", False)
        self.gems = Gems(d.get("gems", {}))


class Gems:
    def __init__(self, d: dict):
        # Task: Re check implementation if required.
        self.enabled = d.get("enabled", False)
        self.tiers = d.get("tiers", {})
        self.gemsToUse = d.get("gemsToUse", {})
        self.disableHuntIfNoGems = d.get("disableHuntIfNoGems", False)
        self.useLowest = d.get("order", {}).get("lowestToHighest", False)


class Cooldowns:
    def __init__(self, d: dict):
        self.longCooldown = d.get("longCooldown", None)
        self.moderateCooldown = d.get("moderateCooldown", None)
        self.shortCooldown = d.get("shortCooldown", None)
        self.briefCooldown = d.get("briefCooldown", None)
        self.captchaRestart = d.get("captchaRestart", None)
        self.commandHandler = CommandHandler(d.get("commandHandler", {}))
        # Reaction Bot
        self.reactionBot = ReactionBot(d.get("reactionBot", {}))


class CommandHandler:
    def __init__(self, d: dict):
        self.betweenCommands = d.get("betweenCommands", None)
        self.readdingToQueue = d.get("beforeReaddingToQueue", 0)


class ReactionBot:
    def __init__(self, d: dict):
        self.huntAndBattle = d.get("huntAndBattle", False)
        self.owo = d.get("owo", False)
        self.prayAndCurse = d.get("prayAndCurse", False)
        self.cooldown = d.get("cooldown", None)

    def get_cd(self):
        if self.cooldown:
            if self.cooldown[0] > self.cooldown[1]:
                raise ValueError("Max cooldown must be greater than min.")

            if self.cooldown[0] == self.cooldown[1]:
                raise ValueError("Both min and max cooldown same..")

            return random.uniform(self.cooldown[0], self.cooldown[1])
        else:
            raise ValueError("No cooldown?")


class Misspell:
    def __init__(self, d: dict):
        self.enabled = d.get("enabled", False)
        self.frequency = d.get("frequencyPercentage", 0)
        self.baseDelay = d.get("baseDelay", None)
        self.rectificationTime = d.get("errorRectificationTimePerLetter", None)

    def should_misspell(self):
        random_num = random.randint(1, 100)
        return random_num > (100 - self.frequency)


class Sleep:
    def __init__(self, d: dict):
        self.enabled = d.get("enabled", False)
        self.frequency = d.get("frequencyPercentage", 0)
        self.checkTime = d.get("checkTime", None)
        self.sleeptime = d.get("sleepTime", None)

        if not 0 <= self.frequency <= 100:
            raise ValueError("Invalid join percent: must be between 0 and 100")

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


class Giveaway:
    def __init__(self, d: dict):
        self.enabled = d.get("enabled", False)
        self.messageRangeToCheck = d.get("messageRangeToCheck", 0)
        self.cooldown = d.get("cooldown", None)
        self.channels = d.get("channelsToJoin", [])

    def get_cd(self):
        if self.cooldown:
            if self.cooldown[0] > self.cooldown[1]:
                raise ValueError("Max cooldown must be greater than min.")

            if self.cooldown[0] == self.cooldown[1]:
                raise ValueError("Both min and max cooldown same..")

            return random.uniform(self.cooldown[0], self.cooldown[1])
        else:
            raise ValueError("No cooldown?")


class BossBattle:
    def __init__(self, d: dict):
        self.enabled = d.get("enabled", False)
        self.joinChance = d.get("joinChancePercent", 0)

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
        self.allottedAmount = d.get("allottedAmount", 0)
        self.goals = GamblingGoals(d.get("goalSystem", {}))

        for cmd in ["coinflip", "slots", "blackjack"]:
            setattr(self, cmd, GambleItem(d.get(cmd, {})))


class GamblingGoals:
    def __init__(self, d: dict):
        self.enabled = d.get("enabled", False)
        self.amount = d.get("amount", 0)


class GambleItem:
    def __init__(self, d: dict):
        self.enabled = d.get("enabled", False)
        self.startValue = d.get("startValue", 0)
        self.multiplier = d.get("multiplierOnLose", 1)
        self.cooldown = d.get("cooldown", None)

        cf_options = d.get("options")
        if cf_options:
            self.options = CoinflipOptions(cf_options)

    def get_cd(self):
        if self.cooldown:
            if self.cooldown[0] > self.cooldown[1]:
                raise ValueError("Max cooldown must be greater than min.")

            if self.cooldown[0] == self.cooldown[1]:
                raise ValueError("Both min and max cooldown same..")

            return random.uniform(self.cooldown[0], self.cooldown[1])
        else:
            raise ValueError("No cooldown?")


class CoinflipOptions:
    def __init__(self, d: dict):
        self.heads = d.get("heads", False)
        self.tails = d.get("tails", False)

    def random_choice(self):
        choices = []
        if self.heads:
            choices.append("h")
        if self.tails:
            choices.append("t")
        return random.choice(choices or ["h"])


class Commands:
    """Contains -> hunt, battle, sell, sac, pray, curse, lvlGrind, cookie, oow, shop, huntbot, lottery
    each with `get_cd` function"""

    def __init__(self, d: dict):
        cmd_list = [
            "hunt",
            "battle",
            "sell",
            "sac",
            "pray",
            "curse",
            "lvlGrind",
            "cookie",
            "owo",
        ]
        for cmd in cmd_list:
            setattr(self, cmd, Command(d.get(cmd, {})))

        self.shop = ShopCommand(d.get("shop", {}))
        self.huntbot = HuntbotCommand(d.get("autoHuntBot", {}))
        self.lottery = Lottery(d.get("lottery", {}))


class Command:
    def __init__(self, d: dict):
        self.enabled = d.get("enabled", False)
        self.cooldown = d.get("cooldown", None)

        # Sell or Sacrifice
        if d.get("rarity"):
            self.rarity = Rarity(d["rarity"])

        # Hunt and Battle
        self.shortform = d.get("useShortForm", None)
        # Hunt only
        self.show_streak = d.get("showStreakInConsole", None)
        self.notify_streak_loss = d.get("notifyStreakLoss", None)

        # Pray and Curse has user id as list while cookie uses int
        # Might need to cleanly handle this later.
        self.user_id = d.get("userid", None)
        self.ping_user = d.get("pingUser", None)
        if d.get("customChannel"):
            self.custom_channel = CustomChannel(d.get("customChannel"))

        # level grind
        self.useQuote = d.get("useQuoteInstead", None)
        self.minLength = d.get("minLengthForRandomString", None)
        self.maxLength = d.get("maxLengthForRandomString", None)

    def get_cd(self):
        if self.cooldown:
            if self.cooldown[0] > self.cooldown[1]:
                raise ValueError("Max cooldown must be greater than min.")

            if self.cooldown[0] == self.cooldown[1]:
                raise ValueError("Both min and max cooldown same..")

            return random.uniform(self.cooldown[0], self.cooldown[1])
        else:
            raise ValueError("No cooldown?")


class Lottery:
    def __init__(self, d: dict):
        self.enabled = d.get("enabled", False)
        self.amount = d.get("amount", 0)


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
            "mythical",
            "legendary",
            "fabled",
            "distorted",
        ]
        for rarity in self._rarities:
            setattr(self, rarity, d.get(rarity, False))

    def get_rarities(self):
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
        self.enabled = d.get("enabled", False)
        self.cooldown = d.get("cooldown", None)
        self.items = ShopItems(d.get("itemsToBuy", {}))

    def get_cd(self):
        if self.cooldown:
            if self.cooldown[0] > self.cooldown[1]:
                raise ValueError("Max cooldown must be greater than min.")

            if self.cooldown[0] == self.cooldown[1]:
                raise ValueError("Both min and max cooldown same..")

            return random.uniform(self.cooldown[0], self.cooldown[1])
        else:
            raise ValueError("No cooldown?")

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
            setattr(self, ring, d.get(f"{ring}Ring", False))


class CustomChannel:
    """
    For Pray and Curse custom channel
    """

    def __init__(self, d: dict):
        self.enabled = d.get("enabled", False)
        self.channel = d.get("channelId", 0)


class HuntbotCommand:
    def __init__(self, d: dict):
        self.enabled = d.get("enabled", False)
        self.cashToSpend = d.get("cashToSpend", 0)
        self.upgrader = HuntbotUpgrader(d.get("upgrader", {}))


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
        self.enabled = d.get("enabled", False)
        self.sleeptime = d.get("sleeptime", None)
        self.traits = HuntbotTraits(d.get("traits", {}))
        self.priorities = HuntbotPriorities(d.get("priorities", {}))

    def get_cd(self):
        # need edit
        if self.sleeptime:
            if self.sleeptime[0] > self.sleeptime[1]:
                raise ValueError("Max cooldown must be greater than min.")

            if self.sleeptime[0] == self.sleeptime[1]:
                raise ValueError("Both min and max cooldown same..")

            return random.uniform(self.sleeptime[0], self.sleeptime[1])
        else:
            raise ValueError("No cooldown?")

    def get_enabled_traits(self):
        enabled_traits = []
        for trait in HUNTBOT_TRAITS:
            if getattr(self.traits, trait):
                enabled_traits.append(trait)
        return enabled_traits


class HuntbotTraits:
    def __init__(self, d: dict):
        for trait in HUNTBOT_TRAITS:
            setattr(self, trait, d.get(trait, False))


class HuntbotPriorities:
    def __init__(self, d: dict):
        for trait in HUNTBOT_TRAITS:
            setattr(self, trait, d.get(trait, 0))


# from pprint import pprint
# import json


def FetchSettings(cnf: dict) -> Settings:
    """
    Returns Settings object based on give config (cnf)
    """
    settings = Settings(cnf)
    """debug_data = json.dumps(
        settings, 
        default=lambda o: o.__dict__ if hasattr(o, '__dict__') else str(o), 
        indent=4
    )
    pprint(debug_data)"""
    return settings
