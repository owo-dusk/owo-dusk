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
import asyncio
import re


async def get_text_from_url(
    image_url: str, session: aiohttp.ClientSession, api_key: str = "helloworld"
):
    url = "https://api.ocr.space/parse/image"
    print(f" Attempting {image_url} url")
    if api_key == "":
        api_key = "helloworld"

    """payload = {
        'apikey': api_key,
        'url': image_url,
        'language': "eng",
        'isOverlayRequired': "true",
        'ocrengine': '2',
        "filetype": "png"
    }"""

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://ocr.space/",
        "Origin": "https://ocr.space",
    }

    try:
        timeout = aiohttp.ClientTimeout(total=15)
        # More safer I suppose
        data = aiohttp.FormData()
        data.add_field("apikey", api_key)
        data.add_field("url", image_url)
        data.add_field("language", "eng")
        data.add_field("isOverlayRequired", "true")
        data.add_field("ocrengine", "2")

        async with session.post(
            url, data=data, headers=headers, timeout=timeout
        ) as response:
            response.raise_for_status()
            result = await response.json()

        if result.get("IsErroredOnProcessing"):
            error_msg = result.get("ErrorMessage")
            print(f"API Error: {error_msg}")

            if "helloworld" in api_key.lower():
                print(
                    "The default demo key could be rate-limited. Please get your own free key at https://ocr.space/ocrapi"
                )
                err = result.get("ErrorMessage")
                if err:
                    print(f"Error : {err}")
            return

        parsed_results = result.get("ParsedResults", [])
        if not parsed_results:
            print("No text found or image could not be read.")
            return

        for page in parsed_results:
            overlay = page.get("TextOverlay")
            if not overlay or not overlay.get("Lines"):
                print("No positional overlay data returned for this page.")
                continue

            result = []
            for line in overlay["Lines"]:
                words = line.get("Words", [])
                x_coord = 0
                y_coord = 0
                if words:
                    x_coord = words[0].get("Left", 0)
                    y_coord = words[0].get("Top", 0)

                text_portion = line.get("LineText")
                # text_portion = next(iter(text_portion)).strip()
                text = re.sub(r"[^a-zA-Z0-9 /]", "", text_portion)
                result.append(
                    {
                        "text": text,
                        "x_axis": int(x_coord),
                        "y_axis": int(y_coord),
                    }
                )

        return result

    except aiohttp.ClientError as e:
        print(f"HTTP Request failed: {e}")
        return None


async def main():
    MY_API_KEY = ""
    TARGET_IMAGE_URL = "https://media.discordapp.net/attachments/989702438317617173/1513592357340319955/reward.png?ex=6a284a3b&is=6a26f8bb&hm=b700db12bb6945492f103ad412576083510ab276a60783503720cb4b0ea6b2e8&=&format=webp&quality=lossless"

    async with aiohttp.ClientSession() as session:
        await get_text_from_url(TARGET_IMAGE_URL, session, api_key=MY_API_KEY)


if __name__ == "__main__":
    asyncio.run(main())
