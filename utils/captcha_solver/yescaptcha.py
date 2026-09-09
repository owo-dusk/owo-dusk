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

import asyncio
import json

import aiohttp
import requests


class captchaClient:
    def __init__(self, api):
        self.api = api
        self.balance = self.get_yescaptcha_balance_sync() or 0
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
        # Will be populated with user id, and store cookies for `owobot.com`
        self._cookie_cache = {}
        self._auth_url = r"https://discord.com/api/v9/oauth2/authorize?client_id=408785106942164992&response_type=code&redirect_uri=https://owobot.com/api/auth/discord/redirect&scope=identify guilds"

    # We aren't supposed to use sync copies for this.. There must be a better solution
    # Double check - for the time being it works!
    def get_yescaptcha_balance_sync(self):
        # At startup its fine to use 0 as fall back.
        # Even if an error causes it to be 0, code would immeidately stop
        # preventing further issues.
        url = "https://api.yescaptcha.com/getBalance"
        try:
            response = requests.post(url, json={"clientKey": self.api}, timeout=10)
            data = response.json()
            return int(data.get("balance", 0)) if data.get("errorId") == 0 else 0
        except Exception:
            return 0

    async def get_yescaptcha_balance(self, session: aiohttp.ClientSession) -> int:
        url = "https://api.yescaptcha.com/getBalance"
        timeout = aiohttp.ClientTimeout(total=10)

        try:
            async with session.post(
                url, json={"clientKey": self.api}, timeout=timeout
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    error_id = data.get("errorId")

                    if error_id == 0:
                        balance = int(data.get("balance", 0))
                        self.balance = balance
                        return balance

                    # Otherwise error_id would be 0 (error)
                    error_code = data.get(
                        "errorCode", "Error field (errorCode) missing"
                    )
                    error_desc = data.get(
                        "errorDescription", "Error field (errorDescription) missing"
                    )
                    print(
                        f"[YesCaptcha Error] API returned error (Code: {error_code}): {error_desc}"
                    )
                else:
                    print(
                        f"[YesCaptcha Error] HTTP request failed with status {response.status}"
                    )

        except aiohttp.ClientError as e:
            print(f"[YesCaptcha Error] Network connection issue: {e}")
        except Exception as e:
            print(f"[YesCaptcha Error] Unexpected error occurred: {e}")

        # fallback
        return self.balance

    async def update_balance(self):
        async with aiohttp.ClientSession() as session:
            self.balance = await self.get_yescaptcha_balance(session)

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
                "websiteKey": "a6a1d5ce-612d-472d-8e37-7601408fbc09",
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

    async def solve_owo_bot_captcha(self, discord_headers, user_id, tries):
        discord_headers["Referer"] = self._auth_url

        # 30 points is required by Yescaptcha for Hcaptcha solving.
        if self.balance < 30:
            print("Not enough balance!")
            return False

        # Check if user has already authenticated
        cookie = self._cookie_cache.get(user_id)
        async with aiohttp.ClientSession(cookies=cookie) as session:
            is_authenticated = False

            # Check if cookie is saved
            if cookie:
                try:
                    async with session.get("https://owobot.com/api/auth") as auth_resp:
                        if auth_resp.status == 200 and await auth_resp.json():
                            print("Using cached OAuth session!")
                            is_authenticated = True
                        else:
                            # Cookie expired or invalid
                            self._cookie_cache.pop(user_id, None)
                except Exception:
                    self._cookie_cache.pop(user_id, None)

            # Perform Discord Authentication
            if not is_authenticated:
                # https://docs.aiohttp.org/en/stable/abc.html#aiohttp.abc.AbstractCookieJar.clear
                session.cookie_jar.clear()

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

                # Follow redirect if present
                try:
                    oauth_json = json.loads(oauth_text)
                    redirect_url = oauth_json.get("location")

                    if redirect_url:
                        async with session.get(redirect_url) as redirect_resp:
                            if redirect_resp.status != 200:
                                print(
                                    f"Redirect failed with HTTP {redirect_resp.status}"
                                )
                                return False
                except Exception as e:
                    print(f"OAuth parsing failed: {e}\nRaw response: {oauth_text}")
                    return False

                # Hit captcha page to ensure session cookies are set
                async with session.get("https://owobot.com/captcha") as captcha_resp:
                    if captcha_resp.status != 200:
                        print(f"Captcha page failed with HTTP {captcha_resp.status}")
                        return False

                # Verify session is active
                async with session.get("https://owobot.com/api/auth") as auth_resp:
                    if auth_resp.status != 200:
                        print(f"Auth check failed with HTTP {auth_resp.status}")
                        return False

                    auth_data = await auth_resp.json()

                if not auth_data:
                    print("Auth data None")
                    return False

                # Save fresh cookies
                # https://docs.aiohttp.org/en/stable/abc.html#aiohttp.abc.AbstractCookieJar.filter_cookies
                self._cookie_cache[user_id] = session.cookie_jar.filter_cookies(
                    "https://owobot.com"
                )

            # Solve Captcha
            try:
                solution = await self.solve_hcaptcha_logic(tries)
                if not solution:
                    print("No solution result found for Hcaptcha")
                    return False
            except Exception as e:
                print(f"Solver Error: {e}")
                return False

            # Verify Solution
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
                    # Update balance may sometimes return `self.balance` as fallback if request fails
                    # Hence we deduct 30 in advance here to take in consideration the points used for the solve.
                    self.balance -= 30
                    # We still attempt to fetch balance since some times if multiple tries was made,
                    # Failed attempts may temporarily consume points, which will take some time to be refunded.
                    await self.update_balance()
                    return True
                else:
                    error_text = await verify_resp.text()
                    print(f"Verification failed (Status {verify_resp.status})")
                    print(f"Server Response: {error_text}")
                    return False
