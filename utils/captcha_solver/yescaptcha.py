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
import requests
import asyncio
import json


class captchaClient:
    def __init__(self, api):
        self.api = api
        self.balance = self.get_yescaptcha_balance() or 0
        self._site_key = "a6a1d5ce-612d-472d-8e37-7601408fbc09"
        self._payload = {
            "authorize": True,
            "integration_type": 0,
            "permissions": "0",
            "location_context": {
                "guild_id": "10000",
                "channel_id": "10000",
                "channel_type": 10000,
            },
        }
        self._auth_url = r"https://discord.com/api/v9/oauth2/authorize?client_id=408785106942164992&response_type=code&redirect_uri=https://owobot.com/api/auth/discord/redirect&scope=identify guilds"

    def get_yescaptcha_balance(self):
        url = "https://api.yescaptcha.com/getBalance"
        try:
            response = requests.post(url, json={"clientKey": self.api}, timeout=10)
            data = response.json()
            return int(data.get("balance", 0)) if data.get("errorId") == 0 else 0
        except Exception:
            return 0

    def update_balance(self):
        self.balance = self.get_yescaptcha_balance()

    async def solve_hcaptcha_logic(self, retries=3):
        """
        Attempts to solve the captcha using Yescaptcha.
        Retries creating a new task 'retries' times upon failure.
        """
        create_url = "https://api.yescaptcha.com/createTask"
        result_url = "https://api.yescaptcha.com/getTaskResult"

        payload = {
            "clientKey": self.api,
            "task": {
                "type": "HCaptchaTaskProxyless",
                "websiteKey": self._site_key,
                "websiteURL": "https://owobot.com",
            },
            "softID": 94493,
        }

        async with aiohttp.ClientSession() as session:
            for attempt in range(retries):
                try:
                    print(f"Solving captcha... Attempt {attempt + 1}/{retries}")

                    async with session.post(create_url, json=payload) as resp:
                        if resp.status != 200:
                            raise Exception(
                                f"Create task failed with HTTP {resp.status}"
                            )
                        data = await resp.json()

                    if data.get("errorId") != 0:
                        raise Exception(f"API Error: {data.get('errorDescription')}")

                    task_id = data.get("taskId")
                    if not task_id:
                        raise Exception("No taskId returned from API")

                    for _ in range(60):
                        await asyncio.sleep(2)

                        async with session.post(
                            result_url,
                            json={"clientKey": self.api, "taskId": task_id},
                        ) as result_resp:
                            if result_resp.status != 200:
                                raise Exception(
                                    f"Result check failed with HTTP {result_resp.status}"
                                )

                            res = await result_resp.json()

                        if res.get("errorId") != 0:
                            # Logic error from solver side
                            raise Exception(
                                f"Polling API Error: {res.get('errorDescription')}"
                            )

                        if res.get("status") == "ready":
                            return res["solution"]["gRecaptchaResponse"]

                    raise Exception("Task timed out without becoming 'ready'")

                except Exception as e:
                    print(f"Attempt {attempt + 1} failed: {e}")
                    if attempt < retries:
                        print("Retrying with a new task...")
                        await asyncio.sleep(1)
                    else:
                        print("All retry attempts exhausted.")

            return None

    async def solve_owo_bot_captcha(self, discord_headers, tries):
        discord_headers["Referer"] = self._auth_url
        self.update_balance()
        if self.balance < 30:
            print("Not enough balance")
            return False

        async with aiohttp.ClientSession() as session:
            # Authorize via Discord
            async with session.post(
                self._auth_url,
                json=self._payload,
                headers=discord_headers,
                allow_redirects=True,
            ) as oauth_resp:
                if oauth_resp.status != 200:
                    print(f"OAuth failed with HTTP {oauth_resp.status}")
                    return False

                oauth_text = await oauth_resp.text()

            # 2. Follow redirect if present
            try:
                oauth_json = json.loads(oauth_text)
                redirect_url = oauth_json.get("location")

                if redirect_url:
                    async with session.get(redirect_url) as redirect_resp:
                        if redirect_resp.status != 200:
                            print(f"Redirect failed with HTTP {redirect_resp.status}")
                            return False
            except Exception as e:
                print(f"OAuth parsing failed: {e}")
                print(f"Raw response: {oauth_text}")
                return False

            # 3. Hit captcha page to ensure session cookies are set
            async with session.get("https://owobot.com/captcha") as captcha_resp:
                if captcha_resp.status != 200:
                    print(f"Captcha page failed with HTTP {captcha_resp.status}")
                    return False

            # 4. Verify session is active
            async with session.get("https://owobot.com/api/auth") as auth_resp:
                if auth_resp.status != 200:
                    print(f"Auth check failed with HTTP {auth_resp.status}")
                    return False

                auth_data = await auth_resp.json()

            if not auth_data:
                print("Auth data None")
                return False

            try:
                solution = await self.solve_hcaptcha_logic(tries)
                if not solution:
                    print("No solution result found for Hcaptcha")
                    return False
            except Exception as e:
                print(f"Solver Error: {e}")
                return False

            async with session.post(
                "https://owobot.com/api/captcha/verify",
                json={"token": solution},
                headers={
                    "Referer": "https://owobot.com/captcha",
                    "Origin": "https://owobot.com",
                    "Accept": "application/json, text/plain, */*",
                    "Content-Type": "application/json",
                },
            ) as verify_resp:
                if verify_resp.status == 200:
                    self.update_balance()
                    return True
                else:
                    error_text = await verify_resp.text()
                    print(f"Verification failed (Status {verify_resp.status})")
                    print(f"Server Response: {error_text}")
                    return False
