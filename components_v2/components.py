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

import aiohttp
import time


def generate_nonce() -> str:
    now_ms = int(time.time() * 1000)
    a = now_ms - 1420070400000
    r = a << 22
    return str(r)


class component_names:
    # All components to be handled
    ACTIONS_ROW_COMPONENT = 1
    BUTTON_COMPONENT = 2
    SELECT_MENU_COMPONENT = 3
    TEXT_INPUT_COMPONENT = 4
    USER_SELECT_MENU_COMPONENT = 5
    ROLE_SELECT_MENU_COMPONENT = 6
    MENTIONABLE_SELECT_MENU_COMPONENT = 7
    CHANNEL_SELECT_MENU_COMPONENT = 8
    # --
    SECTION_COMPONENT = 9
    TEXT_DISPLAY_COMPONENT = 10
    THUMBNAIL_COMPONENT = 11
    MEDIA_GALLERY_COMPONENT = 12
    FILE_COMPONENT_TYPE = 13
    SEPARATOR_COMPONENT = 14
    CONTAINER_COMPONENT = 17
    LABEL_COMPONENT = 18


BUTTON_STYLES = {
    # 6 -> Premium. Unwanted so not including.
    1: "primary",
    2: "secondary",
    3: "success",
    4: "danger",
    5: "link",
}

COMPONENT_NAMES = {
    component_names.ACTIONS_ROW_COMPONENT: "action_row",
    component_names.BUTTON_COMPONENT: "button",
    component_names.SELECT_MENU_COMPONENT: "select_menu",
    component_names.TEXT_INPUT_COMPONENT: "text_input",
    component_names.USER_SELECT_MENU_COMPONENT: "user_select",
    component_names.ROLE_SELECT_MENU_COMPONENT: "role_select",
    component_names.MENTIONABLE_SELECT_MENU_COMPONENT: "mentionable_select",
    component_names.CHANNEL_SELECT_MENU_COMPONENT: "channel_select",
    component_names.SECTION_COMPONENT: "section",
    component_names.TEXT_DISPLAY_COMPONENT: "text_display",
    component_names.THUMBNAIL_COMPONENT: "thumbnail",
    component_names.MEDIA_GALLERY_COMPONENT: "media_gallery",
    component_names.FILE_COMPONENT_TYPE: "file",
    component_names.SEPARATOR_COMPONENT: "separator",
    component_names.CONTAINER_COMPONENT: "container",
    component_names.LABEL_COMPONENT: "label",
}


def get_component_name(i: int):
    return COMPONENT_NAMES[i]


def walker(components: list, message_details=None):
    # We are seperating buttons and components
    # I am doing this because I believe this will make development easier
    BUTTONS_LIST = []
    COMPONENTS_LIST = []

    for component in components:
        section_component = False
        component_type = component.get("type")

        if component_type == component_names.BUTTON_COMPONENT:
            # Accessing -> BUTTON_LIST.{element_name}
            BUTTONS_LIST.append(accessory(component, message_details))
        elif component_type == component_names.SELECT_MENU_COMPONENT:
            COMPONENTS_LIST.append(select_menu(component, message_details))
        elif component_type == component_names.SECTION_COMPONENT:
            # Both accessory and components are bundled together.
            # Currently only a thumbnail or button component..
            section_component = True
            COMPONENTS_LIST.append(section(component, message_details))
        elif component_type == component_names.TEXT_DISPLAY_COMPONENT:
            # Markdown text
            COMPONENTS_LIST.append(text_display(component))
        elif component_type == component_names.THUMBNAIL_COMPONENT:
            # Accessory can be either a thumbail or a button
            # Hence accessory class can be used here.
            COMPONENTS_LIST.append(accessory(component, message_details))
        elif component_type == component_names.MEDIA_GALLERY_COMPONENT:
            COMPONENTS_LIST.append(media_gallery(component))
        elif component_type == component_names.LABEL_COMPONENT:
            COMPONENTS_LIST.append(label(component))

        if not section_component:
            if component.get("components"):
                nested_components_list, nested_buttons_list = walker(
                    component.get("components"), message_details
                )

                COMPONENTS_LIST = COMPONENTS_LIST + nested_components_list
                BUTTONS_LIST = BUTTONS_LIST + nested_buttons_list

            if component.get("accessory"):
                # For ease of development, accessory is going to be treated as either
                # a component or a button since accessory only contains a thumbnail or a button
                cur_accessory = accessory(component["accessory"], message_details)

                if cur_accessory.component_name != "button":
                    COMPONENTS_LIST.append(cur_accessory)
                else:
                    BUTTONS_LIST.append(cur_accessory)

    return COMPONENTS_LIST, BUTTONS_LIST


class emoji:
    def __init__(self, data: dict):
        self.id = int(data.get("id", 0))
        self.name = data.get("name")


class select_menu_options:
    # Menu inside select menu
    def __init__(self, data: dict):
        self.emoji = emoji(data.get("emoji", {}))
        self.label = data.get("label")
        self.value = data.get("value")
        self.description = data.get("description")


class select_menu:
    # Actual select menu
    def __init__(self, component: dict, message_details):
        self.component_name = COMPONENT_NAMES[component["type"]]
        self.options = []
        if component.get("options"):
            for item in component["options"]:
                self.options.append(select_menu_options(item))
        self.custom_id = component.get("custom_id")
        self.placeholder = component.get("placeholder")

        self._message_channel_id = message_details["message_channel"]
        self._message_id = message_details["message_id"]
        self._message_flag = message_details["message_flag"]
        self._author_id = message_details["message_author_id"]

        self._options = []
        for item in self.options:
            self._options.append(item.value)

    async def select(self, values: list, session, headers, guild_id):
        if (
            self._message_channel_id
            and self._message_id
            and self._message_flag
            and self._author_id
        ):
            req_json = {
                "type": 3,
                "application_id": str(self._author_id),
                "guild_id": str(guild_id),
                "channel_id": str(self._message_channel_id),
                "message_id": str(self._message_id),
                "session_id": session,
                "message_flags": int(self._message_flag),
                "data": {
                    "component_type": 3,
                    "custom_id": self.custom_id,
                    "type": 3,
                    "values": values,
                },
            }

            async with aiohttp.ClientSession() as http:
                resp = await http.post(
                    "https://discord.com/api/v9/interactions",
                    json=req_json,
                    headers=headers,
                )

                if resp.status_code != 204:
                    print(
                        f"Component selection failed ({resp.status_code}): {resp.text}"
                    )
                    return False

                return True


class section:
    def __init__(self, component: dict, message_details=None):
        self.component_name = COMPONENT_NAMES[component["type"]]
        self.accessory = accessory(component.get("accessory", {}), message_details)

        self.components, self.buttons = walker(
            component.get("components", []), message_details
        )


class text_display:
    def __init__(self, component: dict):
        self.component_name = COMPONENT_NAMES[component["type"]]
        self.id = component.get("id")
        self.content = component.get("content")


class media_gallery_item:
    def __init__(self, data: dict):
        self.media = media(data.get("media"))
        self.description = data.get("description")


class media_gallery:
    def __init__(self, component: dict):
        self.component_name = COMPONENT_NAMES[component["type"]]
        self.items = []
        for item in component.get("items", []):
            self.items.append(media_gallery_item(item))


class label:
    def __init__(self, component: dict):
        # We are not handling components here because those are modals which isn't necessory (for now)
        self.component_name = COMPONENT_NAMES[component["type"]]
        self.id = component.get("id")
        self.label = component.get("label")
        self.description = component.get("description")


class media:
    def __init__(self, data: dict):
        self.url = data.get("url")
        self.proxy_url = data.get("proxy_url")
        self.placeholder = data.get("placeholder")


"""class button:
    def __init__(self, component: dict):
        # before removing, recheck why you put this here,
        # Not used anywhere it seems
        self.component_name = COMPONENT_NAMES[component["type"]]
        self.style = (
            BUTTON_STYLES[component["style"]] if component.get("style") else None
        )
        self.label = component.get("label")
        self.custom_id = component.get("custom_id")
        if component.get("emoji"):
            self.emoji = emoji(component.get("emoji"))
        self.url = component.get("url")
        self.disabled = component.get("disabled", False)"""


class accessory:
    # Accessory of the message
    # Always a thumbnail or button component!
    def __init__(self, data: dict, message_details=None):
        self.component_name = COMPONENT_NAMES[data.get("type")]
        self.id = data.get("id")
        self.url = data.get("url")
        self.custom_id = data.get("custom_id")
        self.label = data.get("label")
        self.emoji = emoji(data.get("emoji", {}))
        self.disabled = data.get("disabled", False)
        self.description = data.get("description")
        self.type = int(data.get("type", -1))
        self.flags = data.get("flags")
        self.style = BUTTON_STYLES[data["style"]] if data.get("style") else None
        if self.type == -1:
            # I am lazy to properly handle this lol
            # TASK: recheck whatever you did here!
            # (Which I most likely won't be checking..)
            self.type = None
        self.media = media(data.get("media", {}))

        self.is_link_button = self.component_name == "button" and self.url is not None
        self.is_clickable_button = (
            self.component_name == "button"
            and self.custom_id is not None
            and not self.disabled
        )
        if self.is_clickable_button and message_details:
            if (
                message_details["message_channel"]
                and message_details["message_id"]
                and message_details["message_flag"]
                and message_details["message_author_id"]
            ):
                self._message_channel_id = message_details["message_channel"]
                self._message_id = message_details["message_id"]
                self._message_flag = message_details["message_flag"]
                self._author_id = message_details["message_author_id"]

        else:
            self.is_clickable_button = False

    async def click(self, session, headers, guild_id):
        if self.is_clickable_button:
            if (
                self._message_channel_id
                and self._message_id
                and self._message_flag
                and self._author_id
            ):
                req_json = {
                    "type": 3,
                    "application_id": str(self._author_id),
                    "guild_id": guild_id,
                    "channel_id": self._message_channel_id,
                    "message_id": self._message_id,
                    "session_id": session,
                    "message_flags": self._message_flag,
                    "data": {"component_type": 2, "custom_id": self.custom_id},
                }

                async with aiohttp.ClientSession() as http:
                    async with http.post(
                        "https://discord.com/api/v9/interactions",
                        json=req_json,
                        headers=headers,
                    ) as resp:
                        if resp.status != 204:
                            text = await resp.text()
                            print(f"Button click failed ({resp.status}): {text}")
                            return False
                        return True
        else:
            print(
                f"Code attempted to click on a button... but not a clickable button  -> {self.custom_id}"
            )
