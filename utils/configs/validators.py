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


def validateCooldown(cd: list):
    """
    Checks if the cooldown provided is a valid cooldown list or not
    If not valid, the function raises ValueError
    """
    if not cd or not isinstance(cd, list):
        raise ValueError("Expected `list` datatype for cooldown.")

    if len(cd) != 2:
        # List has either less than or more than 2 elements
        raise ValueError("Expected exactly two elements in the cooldown list.")

    if cd[0] > cd[1]:
        raise ValueError("Max cooldown must be greater than min.")

    if cd[0] == cd[1]:
        # Should we consider leniency here?
        raise ValueError("Both min and max cooldown same..")


def validateFrequency(freq):
    """
    Ensures frequency is within 0 to 100
    If not valid, the function raises ValueError
    """
    if not 0 <= freq <= 100:
        raise ValueError("Invalid frequency: must be between 0 and 100")
