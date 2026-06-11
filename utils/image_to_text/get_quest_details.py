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

import re
from utils.image_to_text import image_to_text


def int_gap(x: int, x2: int, mingap: int, maxgap: int) -> bool:
    diff = abs(x - x2)
    return diff >= mingap and diff <= maxgap


def extract_quests(ocr_results: list) -> list[dict]:
    PROGRESS_PATTERN = re.compile(r"^\d+/\d+$")

    # Identify potential quest text and progress items
    progress_items = []
    quest_candidates = []

    for item in ocr_results:
        text = item["text"]  # unwrap the set

        if PROGRESS_PATTERN.match(text.replace(",", "")):
            progress_items.append(item)
        elif len(text) > 4:
            quest_candidates.append(item)

    quests = []

    # remove for sure not quest items
    for candidate in quest_candidates.copy():
        text = candidate["text"].strip().lower()
        blacklist = [
            "claimed",
            "rewards earned",
            "you can claim a new quest",
            "free a slot to receive it",
        ]
        for item in blacklist:
            if item in text:
                quest_candidates.remove(candidate)

    # sort both to be at their close y axis
    quest_candidates.sort(key=lambda d: d["y_axis"])
    progress_items.sort(key=lambda d: d["y_axis"])

    for progress_item in progress_items.copy():
        for candidate in quest_candidates.copy():
            # Y axis difference is exactly 25 on every images
            # Noticed some have 23 though
            # to be safe keeping range somewhat lenient
            if int_gap(candidate["y_axis"], progress_item["y_axis"], 22, 27):
                current, total = progress_item["text"].strip().split("/")

                quests.append(
                    {
                        "quest": candidate["text"].strip().lower(),
                        "progress": progress_item["text"].strip(),
                        "current": int(current),
                        "total": int(total),
                        "complete": int(current) == int(total),
                    }
                )
                quest_candidates.remove(candidate)

    return quests


async def get_quest_details(image_url: str, session, api_key: str = "helloworld"):
    ocr_results = await image_to_text.get_text_from_url(image_url, session, api_key)
    return extract_quests(ocr_results)
