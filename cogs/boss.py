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
# from uwu import MyClient


class Boss(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.boss_tickets = 3
        self.sleeping = True
        self.joined_boss_ids = []
        self.bot.message_dispatcher.register(self.on_component_message)

    @property
    def settings(self):
        return self.bot.settings_dict_temp.boss

    async def cog_load(self):
        if not self.settings.enabled:
            try:
                asyncio.create_task(self.bot.unload_cog("cogs.daily"))
            except ExtensionNotLoaded:
                pass
        else:
            asyncio.create_task(self.time_check())

    async def wait_till_reset_day(self):
        self.sleeping = True
        time_to_sleep = self.bot.calc_time()
        await self.bot.log(f"Sleeping boss battle till {time_to_sleep}", "#143B02")
        await asyncio.sleep(time_to_sleep)
        await self.time_check()
        self.sleeping = False

    async def time_check(self):
        last_reset_ts, self.boss_tickets = await self.bot.fetch_boss_stats()

        if self.boss_tickets > 3 or self.boss_tickets < 0:
            # Termporary fix reverting issues with bad logic in prev version.
            self.bot.reset_boss_ticket()
            self.boss_tickets = 3

        today_midnight_ts = self.bot.pst_midnight_timestamp()

        if not last_reset_ts or last_reset_ts < today_midnight_ts:
            # Resetting incase new run or reset timing
            self.bot.reset_boss_ticket()
            self.boss_tickets = 3

            # update database
            self.bot.update_stats_db("boss", today_midnight_ts)

        self.sleeping = False

    def consume_boss_ticket(self, revert=False):
        if not revert:
            self.boss_tickets -= 1
        else:
            self.boss_tickets += 1
        self.bot.consume_boss_ticket(revert)

    def return_battle_id(self, components):
        for component in components:
            if component.component_name == "media_gallery":
                media_item = component.items[0].media
                if "reward" in media_item.url:
                    return media_item.placeholder

        return None

    def check_if_joined(self, battle_id):
        if battle_id and battle_id not in self.joined_boss_ids:
            return False

        return True

    def should_join_guild(self, channel):
        if self.settings.joinAll:
            if (
                self.settings.ignoreGuilds
                and channel.guild.id in self.settings.ignoreGuilds
            ):
                # Skip incase in guild ignore list.
                return False

            if (
                self.settings.joinGuilds
                and channel.guild.id not in self.settings.joinGuilds
            ):
                # Skip incase in guild not in joinGuilds
                return False
            return True
        elif channel.guild.id == self.bot.cm.guild.id:
            # If not joinAll, then we only join boss battles in local server.
            # Ignores Ignore list, because if local guild is ignored, there is no point 
            # in enabling boss battle.
            return True
        
        return False

    async def on_component_message(self, message):
        if self.boss_tickets <= 0 or self.sleeping:
            if not self.sleeping:
                await self.bot.log(
                    "Don't have enough boss tickets to join boss battle..", "#143B02"
                )
                await self.wait_till_reset_day()
            return

        # Check potential boss battle spam join.
        if message.author.id == self.bot.owo_bot_id:
            if message.components:
                for component in message.components:
                    # Boss Embed
                    if component.component_name == "section":
                        if (
                            component.components[0].content
                            and "runs away" in component.components[0].content
                        ):
                            # Check if battle has already been joined
                            battle_id = self.return_battle_id(message.components)
                            if not battle_id or self.check_if_joined(battle_id):
                                return
                            else:
                                # We won't be handling boss battles already skipped or joined
                                # which will be done below
                                self.joined_boss_ids.append(battle_id)


                            # Boss Fight button
                            if (
                                component.accessory
                                and component.accessory.component_name == "button"
                            ):
                                if component.accessory.custom_id == "guildboss_fight":
                                    boss_channel = await self.bot.fetch_channel(
                                        message.channel_id
                                    )

                                    if boss_channel and self.should_join_guild(boss_channel):
                                        if not self.settings.should_join():
                                            await self.bot.log(
                                                "Skipping boss battle..",
                                                "#6F7C8A",
                                            )
                                            return
                                        self.bot.boss_channel_id = boss_channel.id # Re-Check Logic

                                        await asyncio.sleep(0.5)
                                        if not self.bot.command_handler_status[
                                            "captcha"
                                        ]:
                                            click_status = (
                                                await component.accessory.click(
                                                    self.bot.ws.session_id,
                                                    self.bot.local_headers,
                                                    boss_channel.guild.id,
                                                )
                                            )
                                            if click_status:
                                                await self.bot.log(
                                                    f"Joined Boss battle! -> {boss_channel.guild.name} - {boss_channel.name}", "#B5C1CE"
                                                )
                                                self.consume_boss_ticket()


                    if component.component_name == "text_display":
                        if (
                            "Are you sure you want to use another boss ticket?"
                            in component.content
                        ):
                            await self.bot.log(
                                "Boss battle was already joined.", "#B5C1CE"
                            )
                            # redo changes made earlier..
                            self.consume_boss_ticket(revert=True)

                        if "You don't have any boss tickets!" in component.content:
                            # Reset previous entry
                            self.boss_tickets = 0
                            self.joined_boss_ids = []
                            self.bot.reset_boss_ticket(empty=True)


async def setup(bot):
    await bot.add_cog(Boss(bot))

