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

import json
import os
import tomllib

import utils.config_models as config_models


def load_accounts_dict(file_path="utils/stats.json"):
    try:
        with open(file_path, "r", encoding="utf-8") as config_file:
            return json.load(config_file)
    except (FileNotFoundError, json.JSONDecodeError):
        # Override incase of errors
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as config_file:
            json.dump({}, config_file)
        return {}


with open("config/global_settings.json", "r", encoding="utf-8") as config_file:
    global_settings_dict = config_models.configs.FetchGlobalSettings(
        json.load(config_file)
    )

with open("config/webhookContent.json", "r", encoding="utf-8") as config_file:
    webhook_data_dict = json.load(config_file)


with open("config/captcha.toml", "rb") as f:
    captcha_settings_dict = tomllib.load(f)

with open("config/danger.toml", "rb") as f:
    danger_settings_dict = tomllib.load(f)

with open("config/misc.json", "r", encoding="utf-8") as f:
    misc_dict = json.load(f)
