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

from rich.align import Align
from rich.panel import Panel

owo_dusk_api = "https://echoquill.github.io/owo-dusk-api"

owo_art = r"""
  __   _  _   __       ____  _  _  ____  __ _ 
 /  \ / )( \ /  \  ___(    \/ )( \/ ___)(  / )
(  O )\ /\ /(  O )(___)) D () \/ (\___ \ )  ( 
 \__/ (_/\_) \__/     (____/\____/(____/(__\_)
"""
owo_panel = Panel(Align.center(owo_art), style="purple ", highlight=False)
version = "2.6.8"
# Database version won't be changed unless there is an actual
# need to remake database files
database_version = "2.6.8"
