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

QUEST_IDS = {
    "receive an action from a friend": {"id": "action_receive", "helpable": True},
    "receive curses": {"id": "curse", "helpable": True},
    "receive prayers": {"id": "prayer", "helpable": True},
    "receive cookies": {"id": "cookie", "helpable": True},
    "battle with a friend": {"id": "battle_friend", "helpable": True},
    "earn battle xp": {
        # https://media.discordapp.net/attachments/1513350205263839307/1513842904190287882/quest-rows.png?ex=6a293392&is=6a27e212&hm=6916305aa892f748a7f1063dcd1882096bf53ca6d31d16eea0e3bcdda08ed0ed&=&format=webp&quality=lossless
        "id": "battle_xp",
        "helpable": False,
    },
    "gamble your cowoncy": {"id": "gamble", "helpable": False},
    "defeat bosses": {"id": "boss", "helpable": False},  # need to handle
    "send an action to a friend": {"id": "action_send", "helpable": False},
    "manually hunt": {"id": "hunt", "helpable": False},
    "battle": {"id": "battle", "helpable": False},
    "say owo": {"id": "owo", "helpable": False},
}

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

for rank in animal_ranks:
    QUEST_IDS[f"find {rank} animals"] = {"id": f"find_animal_{rank}", "helpable": False}


def is_helpable(quest_id: str) -> bool:
    data = QUEST_IDS.get(quest_id, {})
    if not data:
        raise ValueError(f"Invalid quest id {quest_id}")

    return data.get("helpable")
