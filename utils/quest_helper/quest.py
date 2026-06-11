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
import utils.timestamp as timestamp
from utils.quest_helper.quest_types import QUEST_IDS
from utils.image_to_text.get_quest_details import get_quest_details
from utils.colors import COLORS


"""
QUEST DETAILS:

{
    "quest": next(iter(candidate["text"])).strip(),
    "progress": next(iter(progress_item['text'])).strip(),
    "current": int(current),
    "total": int(total),
    "complete": int(current) == int(total)
}
"""


# I realise how stupid my initial implementation of auto quest in v1.1.0 was
# Its crazy how much I learned and improved from this project!
class QuestHandler:
    """
    This class is global and shared with other users
    """

    def __init__(self, api: str = "helloworld"):
        # Helpable quests are only stored in Quest Handler
        self.quests: list[dict] = []
        self.bulletine = []
        self.lock = asyncio.Lock()
        self.api_key = api
        if api == "helloworld":
            print(
                f"{COLORS.BOLD_RED} Warning: Using test key `helloworld`. This should only be used for testing. Please edit `OwO-Dusk/config/settings.json` file with your quest api key.\nThis api key is entirely free and can be recieved from: {COLORS.RESET}{COLORS.BOLD_BLUE}https://ocr.space/ocrapi/freekey {COLORS.RESET}"
            )

    async def register_helpable_quest(
        self, quest_detail: dict, userid: int, channel_id: int, guild_id: int
    ):
        """Called by LocalQuestHandler when a helpable quest is found"""
        quest_id = QUEST_IDS.get(quest_detail["quest"].lower())
        quest_id = quest_id["id"]
        if not quest_id:
            print(f"unknown quest: {quest_detail['quest']}")
            return

        async with self.lock:
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
            if quest_id in {"cookie", "pray", "curse"}:
                self.bulletine.append(
                    {
                        "userid": userid,
                        "quest_id": quest_id,
                        "channel_id": channel_id,
                        "guild_id": guild_id,
                        "till": quest_detail["total"] - quest_detail["current"],
                    }
                )

            self.quests.append(data)

    async def claim_quest(self, userid: int, quest_id: str, claim_userid: int) -> bool:
        """With the help of user id and quest id, claim a quest by requested user"""
        if quest_id in {"cookie", "pray", "curse"}:
            print(f"Quest {quest_id} is not claimable")
        async with self.lock:
            for idx, quest in enumerate(self.quests):
                if quest["userid"] == userid and quest["quest_id"] == quest_id:
                    if not self.quests[idx]["claim_userid"]:
                        self.quests[idx]["claim_userid"] = claim_userid
                        return True
        return False

    async def update_progress(
        self, claim_userid: int, quest_userid: int, quest_id: str
    ):
        """
        Updates status and returns current state of the quest
        """
        completed = False
        async with self.lock:
            for idx, quest in enumerate(self.quests):
                if quest["userid"] == quest_userid and quest["quest_id"] == quest_id:
                    if quest_id not in {"cookie", "curse", "pray"}:
                        # we can only claim for other quests
                        if quest["claim_userid"] != claim_userid:
                            return False

                    self.quests[idx]["current"] += 1
                    completed = self.quests[idx]["current"] >= self.quests[idx]["total"]

                    if completed:
                        self.quests[idx]["complete"] = True

                    if quest_id in {"cookie", "curse", "pray"}:
                        await self.update_bulletine_progress(quest_userid, quest_id)

                    return completed, self.quests[idx]["current"]
        return False, None

    async def update_bulletine_progress(
        self, quest_userid: int, quest_id: str, value: int = 1
    ):
        # this may not be required, remove after double checking the mess we wrote in this file
        for idx, bul in enumerate(self.bulletine):
            if bul["userid"] == quest_userid and bul["quest_id"] == quest_id:
                self.bulletine[idx]["till"] -= value
                if self.bulletine[idx]["till"] <= 0:
                    return True
        return False

    async def remove_quest(self, quest_userid: int, quest_id: str):
        """Remove a completed quest from the global quests list"""
        async with self.lock:
            self.quests = [
                q
                for q in self.quests
                if not (q["userid"] == quest_userid and q["quest_id"] == quest_id)
            ]

    def get_available_quests(self, exclude_userid: int | None = None) -> list[dict]:
        """
        Get unclaimed quests excluding (optionally) provided userid
        """
        return [
            q
            for q in self.quests
            if not q["claim_userid"]
            and (exclude_userid is None or q["userid"] != exclude_userid)
        ]

    async def update_registered_quest_totals(
        self, quest_userid: int, quest_id: str, current: int, total: int
    ):
        """Update current/total on an already registered quest in order to merge them
        why? I am lazy to properly handle it and this would be a silly workaround I found
        more proper solution might be to use an id system, so quests can be used for checking again with
        quest image for future validation"""
        async with self.lock:
            for idx, quest in enumerate(self.quests):
                if quest["userid"] == quest_userid and quest["quest_id"] == quest_id:
                    self.quests[idx]["current"] = current
                    self.quests[idx]["total"] = total
                    break
            if quest_id in {"cookie", "curse", "pray"}:
                # bulletine
                for idx, bul in enumerate(self.bulletine):
                    if bul["userid"] == quest_userid and bul["quest_id"] == quest_id:
                        val = total - current
                        self.bulletine[idx]["till"] = val


class LocalQuestHandler:
    def __init__(self, qh: QuestHandler, userid: int, session):
        self.qh = qh
        self.userid = userid
        self.session = session
        # `is_timestamp_set` helps determine if this is the first run or
        # whether previous quests have been solved
        # `is_updated` is a flag to check if the quest is uptodate after a success
        # (updated with new quest details)
        self.is_timestamp_set = False
        self.next_quest_timestamp = 0
        self.is_updated = False

        # full local quest list for a user
        self.quests: list[dict] = []
        #

    async def update_quests(
        self, url: str, channel_id: int, guild_id: int, next_quest_timestamp: int
    ):
        """
        From the url provided, this function fetches quests and saves them locally
        also helpable quests are pushed to the help list (qh)

        only pushes if quest not already being handled
        (I hope this doesn't cause issues when same type of quest appears twice
        but since its rare, lets leave it to the future me to handle!)
        """
        fresh_quests = await get_quest_details(url, self.session, self.qh.api_key)

        existing_ids = {q["quest_id"] for q in self.quests}

        self.quests = []
        recorded_quest_ids = []
        for quest in fresh_quests:
            quest_info = QUEST_IDS.get(quest["quest"].lower(), {})
            quest_id = quest_info.get("id")
            if not quest_id:
                print(f"unknown quest: {quest['quest']}")
                continue

            if quest["complete"]:
                print(f"completed quest: {quest['quest']}")
                continue

            if quest_id not in recorded_quest_ids:
                recorded_quest_ids.append(quest_id)

                self.quests.append(
                    {
                        "quest": quest["quest"].lower(),
                        "quest_id": quest_id,
                        "current": quest["current"],
                        "total": quest["total"],
                        "complete": quest["complete"],
                        "helpable": quest_info.get("helpable", False),
                    }
                )

                is_helpable = quest_info.get("helpable", False)
                is_new = quest_id not in existing_ids

                if is_helpable and is_new and not quest["complete"]:
                    await self.qh.register_helpable_quest(
                        quest, self.userid, channel_id, guild_id
                    )
            else:
                # To avoid issues when claiming, we treat both quests as one quest
                # a lazy approah, which would have done better with an id system
                # but well lack of time
                for idx, qs in enumerate(self.quests):
                    if qs["quest_id"] == quest_id:
                        self.quests[idx]["current"] += quest["current"]
                        self.quests[idx]["total"] += quest["total"]

                        if qs["helpable"]:
                            await self.qh.update_registered_quest_totals(
                                self.userid,
                                quest_id,
                                self.quests[idx]["current"],
                                self.quests[idx]["total"],
                            )
                        break

        self.update_next_timestamp(next_quest_timestamp)

    async def sync_progress(self, quest_id: str, current: int, completed: bool):
        """
        Called locally before performing actions on LocalQuestHandler
        Helps ensures progress is up-to-date
        """
        for idx, quest in enumerate(self.quests):
            if quest["quest_id"] == quest_id:
                self.quests[idx]["current"] = current
                if completed:
                    self.quests[idx]["complete"] = True
                    # when we validate externaly, especially during refresh, we should
                    # be able to handle false quest completes
                    await self.qh.remove_quest(self.userid, quest_id)
                break

    def get_self_doable_quests(self) -> list[dict]:
        return [q for q in self.quests if not q["complete"] and not q["helpable"]]

    def help_required(self) -> bool:
        temp = [q for q in self.quests if not q["complete"] and q["helpable"]]
        if temp:
            return True
        return False

    def get_helpable_quests(self) -> list[dict]:
        return self.qh.get_available_quests(self.userid)

    def get_all_quests(self) -> list[dict]:
        """REturns all the quests"""
        return self.quests

    def update_next_timestamp(self, timestamp):
        """
        Updates timestamp till next claimable quest
        """
        self.next_quest_timestamp = timestamp
        self.is_timestamp_set = True

    async def wait_till_next_quest_rest(self):
        datetime_timestamp = timestamp.discord_timestamp_to_datetime(
            self.next_quest_timestamp
        )
        time_to_wait = timestamp.calc_time_till_timestamp(datetime_timestamp)
        if time_to_wait > 0:
            print(f"sleeping till {time_to_wait}")
            await asyncio.sleep(time_to_wait)
