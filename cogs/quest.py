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
import re
import json

from discord.ext.commands import ExtensionNotLoaded
from discord.ext import commands, tasks
from cogs._BASE import BaseCog

try:
    with open("utils/emojis.json", "r", encoding="utf-8") as file:
        emoji_dict = json.load(file)
except FileNotFoundError:
    print("The file emojis.json was not found.")
except json.JSONDecodeError:
    print("Failed to decode JSON from the file.")


def has_ranked_emoji(self, text, rank, emoji_dict=emoji_dict):
    """
    Takes message and rank to figure out if rank exists in the hunt message
    """
    pattern = re.compile(
        r"<a:[a-zA-Z0-9_]+:[0-9]+>|:[a-zA-Z0-9_]+:|[\U0001F300-\U0001F6FF\U0001F700-\U0001F77F]"
    )
    emojis = pattern.findall(text)

    for emoji in emojis:
        emoji_data = emoji_dict.get(emoji)
        # Check if rank matches that of emoji_dict
        if emoji_data and emoji_data["rank"] == rank:
            return True

    return False


animal_ranks = [
    "common",
    "uncommon",
    "rare",
    "epic",
    "special",
    "mythical",
    "gem",
    "legendary",
    "fabled",
    "distorted",
    "hidden",
]

# NOTE: Never use quest details fetched as a means to validate
# they may be edited in certain cases, for eg. when multiple of same quest
# inorder to work properly

"""

UPDATE ongoing_battle_external_quest FLAG B4 RELEASE!
"""


class Quest(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.timed_task = None  # track active timed task so we can cancel it
        self.quest_cmd = {
            "cmd_name": self.bot.alias["quest"]["normal"],
            "prefix": True,
            "checks": True,
            "id": "quest",
        }
        self.all_quests_done = False
        self.alr_posted = False
        self.bot.message_dispatcher.register(self.on_component_message)
        self.catcha_a_rank = ""
        self.quest_self_doable = {
            "battle_xp": {"quest": False, "till": 0},
            "gamble": {"quest": False, "till": 0},
            "boss": {"quest": False, "till": 0},
            "action_send": {"quest": False, "till": 0},
            "hunt": {"quest": False, "till": 0},
            "battle": {"quest": False, "till": 0},
            "owo": {"quest": False, "till": 0},
        }
        for rank in animal_ranks:
            self.quest_self_doable[f"find_animal_{rank}"] = {"quest": False, "till": 0}

        self.repeat_quest_flag = False

    def get_quest_cmd(self, channel=None):
        cmd = self.quest_cmd.copy()
        if not channel:
            return cmd
        else:
            cmd["channel"] = channel

    @property
    def settings(self):
        return self.bot.settings_dict.autoQuest

    @property
    def is_gamble_enabled(self):
        sett = self.bot.settings_dict.gamble
        cf = sett.coinflip.enabled
        slots = sett.slots.enabled
        bj = sett.blackjack.enabled
        return cf or slots or bj

    async def cog_load(self):
        # its not smart to use `await`able functions here, double check!
        if (
            not self.settings.enabled
            or not self.bot.danger_settings_dict["allow_auto_quest"]
        ):
            if not self.bot.danger_settings_dict["allow_auto_quest"]:
                await self.bot.log(
                    "Current Auto quests is in a experimental stage. Inorder to avoid issues, we have locked auto quest until user manually alows it from `owo-dusk/config/danger.toml` file. Check the file for more details!",
                    "#e6e65a",
                )
            try:
                asyncio.create_task(self.bot.unload_cog("cogs.quest"))
            except ExtensionNotLoaded:
                pass
        else:
            reaction_bot_settings = self.bot.settings_dict.cooldowns.reactionBot
            if (
                reaction_bot_settings.huntAndBattle
                or reaction_bot_settings.owo
                or reaction_bot_settings.prayAndCurse
            ):
                await self.bot.log(
                    "Currently `helpOthers` doesn't work with reactionbot. There were some issues with reaction bot and quest. This will be doable once `autoQuest` comes out of experimental mode in future updates. You may continue using as is, but it would be better to disable reactionbot while using autoQuest for the best experience!",
                    "#e6e65a",
                )
            self.main_quest_loop.start()

    def is_valid_quest(self, components):
        section_components = None
        for comp in components:
            if comp.component_name == "section":
                section_components = comp.components
                break

        if not section_components:
            return False

        for comp in section_components:
            if comp.content and f"<@{self.bot.user.id}>'s Quest Log" in comp.content:
                return True

        return False

    def get_quest_url(self, components):
        for comp in components:
            if comp.component_name == "media_gallery":
                url = comp.items[0].media.url
                if "quest-rows" in url:
                    return url
        return None

    def get_available_quest_details(self, components, buttons):
        """
        Checks if quest is valid first, If valid then it
        checks if there is any claimable or doable quests available.
        """
        res = {
            "claimBtn": None,
            "url": "",
            "questDone": False,
            "next_quest_timestamp": 0,
        }

        # Check for available quests
        for btn in buttons:
            if btn.custom_id == "quests:claim":
                if not btn.disabled:
                    # Quests claimable
                    res["claimBtn"] = btn

        # Check if quest quest is completed for the day
        for comp in components:
            if comp.component_name == "text_display":
                if "UwU You finished all of your quests!" in comp.content:
                    res["questDone"] = True

                if "next quest" in comp.content:
                    timestamp = re.search(r"<t:(\d+):f>", comp.content.lower())
                    if timestamp:
                        res["next_quest_timestamp"] = int(timestamp.group(1))

        if not res["questDone"]:
            # Fetch quest Image url
            url = self.get_quest_url(components)
            res["url"] = url

        return res

    """def is_quests_updated(self):
        pass"""

    async def handle_self_quests(self, quests):
        """Do quests we can do ourselfs, Blocking.."""
        # Update quest stats
        for quest in quests:
            quest_id = quest["quest_id"]

            self.quest_self_doable[quest_id]["quest"] = True
            # only passing how much we actually need to do
            self.quest_self_doable[quest_id]["till"] = quest["total"] - quest["current"]

        # Handle quests
        for quest in quests.copy():
            quest_id = quest["quest_id"]
            quest_till = self.quest_self_doable[quest_id]["till"]
            # Reset values to be safe
            self.catcha_a_rank, self.repeat_quest_flag = "", False
            # 1. hunt
            if not self.get_cmd_cnf("hunt").enabled and self.settings.canEnable:
                if "find_animal_" in quest_id:
                    self.catcha_a_rank = quest_id.replace("find_animal_", "")
                    await self.bot.log(
                        f"Attempting to do quest - catch pet of {self.catcha_a_rank} (hunt)",
                        color="#a5c7e3",
                    )
                    await self.handle_repeat_quest("hunt")

                elif quest_id == "hunt":
                    await self.bot.log(
                        f"Attempting to do quest - running hunt x{quest_till}",
                        color="#a5c7e3",
                    )
                    await self.handle_repeat_quest("hunt", quest_till)
            elif not self.get_cmd_cnf("battle").enabled and self.settings.canEnable:
                if quest_id == "battle_xp":
                    await self.bot.log(
                        f"Attempting to do quest - gain {quest_till} xp from battle",
                        color="#a5c7e3",
                    )
                    await self.handle_repeat_quest("battle")

                elif quest_id == "battle":
                    await self.bot.log(
                        f"Attempting to do quest - running battle x{quest_till}",
                        color="#a5c7e3",
                    )
                    await self.handle_repeat_quest("battle", quest_till)

            elif not self.get_cmd_cnf("owo").enabled and self.settings.canEnable:
                if quest_id == "owo":
                    await self.bot.log(
                        f"Attempting to do quest - send owo x{quest_till}",
                        color="#a5c7e3",
                    )
                    await self.handle_repeat_quest("owo", quest_till)
            elif quest_id == "gamble":
                if not self.is_gamble_enabled and self.settings.canEnable:
                    await self.bot.log(
                        f"Attempting to do quest - running gamble commands x{quest_till}",
                        color="#a5c7e3",
                    )
                    await self.handle_repeat_quest(
                        self.bot.random.choice(["slots", "coinflip"]), quest_till
                    )

            elif quest_id == "action_send":
                await self.bot.log(
                    f"Attempting to do quest - sending actions x{quest_till}",
                    color="#a5c7e3",
                )
                await self.handle_action_quest(quest_till)

    async def handle_helpable_quests(self, quests):
        """Quests others can't do themselves, Blocking.."""
        """
        Quests Format:

        data = {
            "userid": userid,
            "current": quest_detail["current"],
            "total": quest_detail["total"],
            "complete": quest_detail["complete"],
            "claim_userid": None,
            "quest_id": quest_id,
            "channel_id": channel_id,
            "guild_id": guild_id,
        }
        """
        chnl, user = None, None
        if not quests:
            return

        await self.bot.log("Attempting to help other quests", color="#a5c7e3")

        for quest in quests:
            quest_id = quest["quest_id"]
            # Try see if user's channel is fetchable
            try:
                chnl = await self.bot.fetch_channel(quest["channel_id"])
            except Exception:
                chnl = None

            # see if user is in our guild
            try:
                user = await self.bot.cm.guild.fetch_member_profile(quest["userid"])
            except Exception:
                user = None

            if not (chnl or user):
                continue
            else:
                if quest_id not in {"cookie", "pray", "curse"}:
                    success = await self.bot.quest_handler.qh.claim_quest(
                        quest["userid"], quest_id, self.bot.user.id
                    )
                else:
                    success = True

            # Handle quest
            if success:
                till = quest["total"] - quest["current"]
                channel = chnl.id if chnl else None
                if quest_id == "action_receive":
                    await self.handle_action_quest(till=till)

                elif quest_id == "battle_friend":
                    await self.bot.log(
                        f"Attempting to help {quest['userid']} with {quest_id}",
                        color="#a5c7e3",
                    )
                    if (
                        not self.get_cmd_cnf("battle").enabled
                        and self.settings.canEnable
                    ):
                        await self.handle_repeat_quest(
                            "battle", till, f"<@{quest['userid']}>"
                        )
                    else:
                        self.bot.quest_help_request["battle"]["channel"] = channel
                        self.bot.quest_help_request["battle"]["till"] = till
                        self.bot.quest_help_request["battle"]["userid"] = quest[
                            "userid"
                        ]
                        self.bot.quest_help_request["battle"]["enabled"] = True

                elif quest_id in {"cookie", "pray", "curse"}:
                    enabled = False
                    if quest_id != "cookie":
                        # why? since curse and pray cooldown is shared!
                        enabled = (
                            self.get_cmd_cnf("pray").enabled
                            or self.get_cmd_cnf("curse").enabled
                        )
                    else:
                        cnf = self.get_cmd_cnf(quest_id)
                        enabled = cnf.enabled
                    await self.bot.log(
                        f"Attempting to help {quest['userid']} with {quest_id}",
                        color="#a5c7e3",
                    )
                    if not enabled and self.settings.canEnable:
                        # if not chnl, it will be same guild. we may send in our own channel if same guild

                        await self.handle_repeat_quest(
                            quest_id,
                            till,
                            f"<@{quest['userid']}>",
                            quest["userid"],
                            quest_id,
                            channel,
                        )
                    else:
                        self.bot.quest_help_request[quest_id]["channel"] = channel
                        self.bot.quest_help_request[quest_id]["till"] = till
                        self.bot.quest_help_request[quest_id]["userid"] = quest[
                            "userid"
                        ]
                        self.bot.quest_help_request[quest_id]["enabled"] = True
                    await self.wait_till_unclaimable_quest_done()

    async def wait_till_unclaimable_quest_done(self):
        qsts = ["cookie", "curse", "pray", "battle"]
        while True:
            any_enabled = any(
                self.bot.quest_help_request[qst]["enabled"] for qst in qsts
            )
            if not any_enabled:
                break
            await asyncio.sleep(30)

    async def handle_action_quest(self, till: int, userid=None, channelid=None):
        actions = ["stare", "kill", "greet", "punch", "wave", "slap"]
        action_cmd = {
            "cmd_name": "",
            "cmd_arguments": "<@678344927997853742>" if not userid else f"<@{userid}>",
            "prefix": True,
            "checks": True,
            "id": "action",
            "channel": channelid,
        }

        for _ in range(till):
            action = self.bot.random.choice(actions)
            action_cmd["cmd_name"] = action
            await self.bot.put_queue(action_cmd)
            await self.bot.sleep_till([4, 6])
            if userid:
                # update quest progress
                current, completed = await self.bot.quest_handler.qh.update_progress(
                    self.bot.user.id, userid, "action_receive"
                )
                if current is not None:
                    await self.bot.quest_handler.sync_progress(
                        "action_receive", current, completed
                    )
                if completed:
                    break

    def get_cmd_cnf(self, key: str):
        base_cnf = self.bot.settings_dict.commands
        if key in {"slots", "coinflip"}:
            base_cnf = self.bot.settings_dict.gamble
        return getattr(base_cnf, key)

    def check(self, message, content, channel_id=None):
        return (
            message.author.id == self.bot.user.id
            and message.channel.id == (channel_id if channel_id else self.bot.cm.id)
            and message.content == content
        )

    async def block_till_send(self, content, channel_id=None, prefix=False, arg=None):
        if prefix:
            content = f"{self.bot.settings_dict.prefix}{content}"
        if arg:
            content += f" {arg}"
        try:
            await self.bot.wait_for(
                "message",
                check=lambda m: self.check(m, content, channel_id),
                timeout=30.0,
            )
        except asyncio.TimeoutError:
            print("this is bad, check failed miserably!")

    async def handle_repeat_quest(
        self,
        cmd_name,
        till: int = None,
        arg: str = None,
        upd_userid: int = None,
        upd_questid: str = None,
        chn_to_send: int = None,
    ) -> bool:
        """
        Repeat quest handles repeated sending of commands
        The end of this loop is either determined by `till` if provided
        or the external flag `self.repeat_quest_flag` being set to true

        Just incase when dashboard gets added, and user manually enables the disabled command, we
        exit partially
        """

        user_till_value = True if till else False

        while True:
            cmd = {
                "cmd_name": cmd_name,
                "cmd_arguments": "1" if cmd_name in {"slots", "coinflip"} else arg,
                "prefix": True if cmd_name != "owo" else False,
                "checks": True,
                "id": cmd_name if cmd_name != "curse" else "pray",
                "channel": chn_to_send,
            }
            cnf = self.get_cmd_cnf(cmd_name)

            if cnf.enabled:
                return False

            else:
                if self.repeat_quest_flag:
                    self.repeat_quest_flag = False
                    break

            await self.bot.put_queue(cmd)
            if user_till_value:
                # the rest - battle xp and the hunt rank one, will be updated from on_message
                await self.block_till_send(
                    cmd_name, chn_to_send, cmd["prefix"], cmd["cmd_arguments"]
                )
                await self.bot.remove_queue(
                    id=cmd_name if cmd_name != "curse" else "pray"
                )

            if upd_questid and upd_userid:
                current, completed = await self.bot.quest_handler.qh.update_progress(
                    self.bot.user.id, upd_userid, upd_questid
                )
                if current is not None:
                    await self.bot.quest_handler.sync_progress(
                        upd_questid, current, completed
                    )
                if completed:
                    break

            if user_till_value:
                till -= 1
                if till <= 0:
                    break

            await self.bot.sleep(cnf.get_cd())

        return True

    @tasks.loop()
    async def main_quest_loop(self):
        """
        Initially all accounts will do their own quests
        before starting to help others..
        There should be sufficient time in-between next quest for this

        TASK: make sure done quests are being updated!
        and those re-fetched ones as well!
        """
        await asyncio.sleep(self.settings.get_cd())
        # 1. Put queue to quest command
        await self.bot.put_queue(self.quest_cmd)
        await self.bot.sleep_till([5, 10])

        # 2. if help required, post
        if self.bot.quest_handler.help_required() and self.settings.useHelpChannel:
            if not self.alr_posted:
                await self.bot.put_queue(self.get_quest_cmd(self.settings.channelId))
                self.alr_posted = True

        # 3. If self doable quests, then do them!
        self_doable = self.bot.quest_handler.get_self_doable_quests()
        await self.handle_self_quests(self_doable)

        # 4. Help other quest users
        if self.settings.helpOthers:
            helpable = self.bot.quest_handler.get_helpable_quests()
            await self.handle_helpable_quests(helpable)

        # 5. either sleep or continue
        if self.all_quests_done:
            print(f"retiring {self.bot.user.name}")
            self.all_quests_done = False
            self.alr_posted = False
            await self.bot.quest_handler.wait_till_next_quest_rest()

    async def on_component_message(self, message):
        if message.author.id != self.bot.owo_bot_id:
            return

        if message.channel_id != self.bot.cm.id:
            return

        components, buttons = message.components, message.buttons
        if self.is_valid_quest(components):
            # Remove quest command that was queued
            await self.bot.remove_queue(id="quest")
            # Fetch quest details
            quest_details = self.get_available_quest_details(
                components=components, buttons=buttons
            )
            # The quest would get edited, sure but
            # the image we fetched earlier wouldn't change
            quest_channel = await self.bot.fetch_channel(message.channel_id)

            if quest_details["claimBtn"]:
                await quest_details["claimBtn"].click(
                    self.bot.ws.session_id,
                    self.bot.local_headers,
                    quest_channel.guild.id,
                )
                await self.bot.log("Claimed a finished quest!", color="#a5c7e3")

            if quest_details["questDone"]:
                await self.bot.log(
                    "User has finished all of their quests!", color="#a5c7e3"
                )
                self.all_quests_done = True

            next_quest_timestamp = quest_details["next_quest_timestamp"]

            # Fetch quests from the fetched image
            # and Update the fetched quest to quest_handler

            # Whether http or https, both must be in url. otherwise invalid.
            if not quest_details["questDone"] and "http" in quest_details["url"]:
                await self.bot.log("Trying to update quest lists...", color="#a5c7e3")
                await self.bot.quest_handler.update_quests(
                    quest_details["url"],
                    self.bot.cm.id,
                    self.bot.cm.guild.id,
                    next_quest_timestamp,
                )

    @commands.Cog.listener()
    async def on_message(self, message):
        nick = self.bot.get_nick(message)

        if not (
            message.channel.id == self.bot.cm.id
            and message.author.id == self.bot.owo_bot_id
        ):
            return

        if self.catcha_a_rank and self.quest_self_doable["hunt"]["quest"]:
            # Hunt rank check
            if nick not in message.content:
                return

            if (
                "you found:" in message.content.lower()
                or "caught" in message.content.lower()
            ):
                # Valid hunt message
                if has_ranked_emoji(self, message.content, self.catcha_a_rank):
                    self.quest_self_doable["hunt"]["till"] -= 1
                    if (
                        0 >= self.quest_self_doable["hunt"]["till"]
                    ) and not self.repeat_quest_flag:
                        self.repeat_quest_flag = True

        if self.quest_self_doable["battle"]["quest"]:
            # battle xp update
            xp = None
            if message.embeds:
                for embed in message.embeds:
                    if (
                        embed.author.name is not None
                        and f"{self.bot.user.display_name} goes into battle!"
                        in embed.author.name
                    ):
                        if embed.footer:
                            xp = int(
                                re.search(r"\+([\d,]+) xp", embed.footer.text)
                                .group(1)
                                .replace(",", "")
                            )
                            break

            if xp:
                self.quest_self_doable["battle"]["till"] -= xp
                if 0 >= self.quest_self_doable["battle"]["till"]:
                    if not self.repeat_quest_flag:
                        self.repeat_quest_flag = True


async def setup(bot):
    await bot.add_cog(Quest(bot))
