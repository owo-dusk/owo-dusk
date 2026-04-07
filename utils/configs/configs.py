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

from utils.configs.settings import Settings
from utils.configs.globalSettings import GlobalSettings


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


def FetchGlobalSettings(cnf: dict) -> GlobalSettings:
    """
    Returns Settings object based on give config (cnf)
    """
    settings = GlobalSettings(cnf)

    return settings
