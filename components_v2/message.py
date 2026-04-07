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

from components_v2.components import walker


class author:
    # The user who send the message.
    def __init__(self, data: dict):
        self.name = data.get("username")
        self.id = int(data.get("id", 0))


class emoji:
    # Emoji, likely to be inside `button`
    def __init__(self, data: dict):
        self.id = int(data.get("id", 0))
        self.name = data.get("name")


class message:
    # Message object
    def __init__(self, data: dict):
        self.author = author(data.get("author", {}))
        self.id = int(data.get("id", 0))
        self.flags = int(data.get("flags", 0))
        self.content = data.get("content", "")
        self.channel_id = int(data.get("channel_id", 0))
        self.components, self.buttons = walker(
            components=data.get("components", {}),
            message_details={
                "message_channel": self.channel_id,
                "message_id": self.id,
                "message_flag": self.flags,
                "message_author_id": self.author.id,
            },
        )


def get_message_obj(msg: str):
    return message(msg)
