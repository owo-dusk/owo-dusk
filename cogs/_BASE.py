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

"""
THIS FILE PURELY EXISTS FOR TYPEHINTS,
ignore!
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from discord.ext import commands

if TYPE_CHECKING:
    # Always false at runtime!
    from uwu import MyClient


class BaseCog(commands.Cog):
    def __init__(self, bot: MyClient):
        self.bot = bot
