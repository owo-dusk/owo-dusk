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

from discord.ext import commands
import asyncio
from discord.ext.commands import ExtensionNotLoaded

"""
TASK: recheck set_stat
imporve logging in here.
"""

class Mail(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.message_dispatcher.register(self.on_component_message)
        self.bot.message_dispatcher.register(self.on_component_message_edit, edit=True)

        self.cmd = {
            "cmd_name": "mail",
            "cmd_arguments": None,
            "prefix": True,
            "checks": True,
            "id": "mail",
        }

        # We store section components here. This is because when we view the mail, there is no
        # proper way to check if the mail is ours or not. So we store mails to go through to compare
        # then click.
        self.data = []

        # Message Id also does not change when message is edited.
        self.message_id = 0

    def get_section_content_and_button(self, components):
        """
        Open Mail -> opened_mail
        Closed Mail -> closed_mail
        style -> 2 -> claimed
        style -> 1 -> unclaimed
        """
        data = []
        for component in components:
            if component.component_name == "section":
                print(component, component.buttons, component.components)
                if component.accessory.style == "primary":
                    data.append({
                        "content": component.components[0].content,
                        "button": component.accessory
                    })

        return data

    def fetch_claim_btn(self, components):
        for component in components:
            if component.component_name == "section":
                comp = component.components[0]
                if "Reward" in comp.content:
                    if not component.accessory.disabled:
                        return component.accessory
        return None


    def is_page_left(self, buttons):
        pages = []
        for btn in buttons:
            if btn.custom_id == "noop":
                pages = btn.label.replace("/", " ").split()
        if not pages:
            return False

        return int(pages[0]) < int(pages[1])

    async def cog_load(self):
        if not self.bot.settings_dict_temp.mail:
            try:
                asyncio.create_task(self.bot.unload_cog("cogs.mail"))
            except ExtensionNotLoaded:
                pass


    async def on_component_message(self, message):
        if message.channel_id != self.bot.cm.id:
            return
        # Add channel check!

        for component in message.components:
            if component.component_name == "section":
                first_comp = component.components[0]
                if first_comp.component_name == "text_display":
                    if (
                        first_comp.content
                        == f"📫 **| {self.bot.user.display_name}**, you have **2** unread mail!"
                    ):
                        # Unread mail detected!
                        await self.bot.set_stat(False)
                        await self.bot.log("Mail(s) detected! Attempting to claim..", "#4c9d9e")
                        if component.buttons[0].custom_id == "show_mail":
                            channel = await self.bot.fetch_channel(message.channel_id)
                            if channel:
                                await component.buttons[0].click(
                                    self.bot.ws.session_id,
                                    self.bot.local_headers,
                                    channel.guild.id,
                                )

            elif component.component_name == "text_display":
                if component.content == f"## 📫 <@{self.bot.user.id}>'s Mailbox":
                    # Mailbox detected! - When Unread mail reminder is clicked, this shows up.
                    channel = await self.bot.fetch_channel(message.channel_id)
                    # Fetches valid sections to click.
                    self.data = self.get_section_content_and_button(message.components)
                    self.message_id = message.id

                    if not self.data:
                        # We release the lock on commands here, no pages left.
                        # And we reset message_id
                        await self.bot.set_stat(True)
                        self.message_id = 0


                    await self.data[0]["button"].click(
                        self.bot.ws.session_id,
                        self.bot.local_headers,
                        channel.guild.id,
                    )

    async def on_component_message_edit(self, message):
        if message.id != self.message_id:
            return

        for component in message.components:
            if component.component_name == "text_display":
                if component.content == f"## 📫 <@{self.bot.user.id}>'s Mailbox":
                    # Mail Box edit - When back button is clicked.
                    self.data = self.get_section_content_and_button(message.components)

                    if self.data:
                        channel = await self.bot.fetch_channel(message.channel_id)

                        await self.data[0]["button"].click(
                            self.bot.ws.session_id,
                            self.bot.local_headers,
                            channel.guild.id,
                        )

                    elif self.is_page_left(message.buttons):
                        # If more pages is left, click "Next"
                        for btn in message.buttons:
                            if btn.custom_id == "paged_next":
                                await btn.click(
                                    self.bot.ws.session_id,
                                    self.bot.local_headers,
                                    channel.guild.id,
                                )
                                break
                    else:
                        # We release the lock on commands here, no pages left.
                        # And we reset message_id
                        await self.bot.set_stat(True)
                        self.message_id = 0
                    break

                elif "## You broke" in component.content:
                    channel = await self.bot.fetch_channel(message.channel_id)
                    # Broke streak part:
                    # Could be either claimed or unclaimed.

                    btn = self.fetch_claim_btn(message.components)
                    if btn:
                        await self.bot.log("Mail Claimed..", "#4c9d9e")
                        await btn.click(
                            self.bot.ws.session_id,
                            self.bot.local_headers,
                            channel.guild.id,
                        )
                        return

                    # Failed to fetch button, return.
                    for btn in message.buttons:
                        """if btn.label == "Claim":
                            # Claim the mail!
                            await btn.click(
                                self.bot.ws.session_id,
                                self.bot.local_headers,
                                channel.guild.id,
                            )
                            return"""
                        if btn.custom_id == "mail_back":
                            # We return here since claim button should appear before
                            # This part in the buttons list.
                            await btn.click(
                                self.bot.ws.session_id,
                                self.bot.local_headers,
                                channel.guild.id,
                            )
                            return

                    # If neither we reset states. This isnt suppossed to trigger.
                    # Task: Log error here.
                    await self.bot.set_stat(True)
                    self.message_id = 0


async def setup(bot):
    await bot.add_cog(Mail(bot))
