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

import aiohttp

url = "https://owobot.com/api/status"


def get_max_shards(json_data):
    max_shard = -1
    for item in json_data:
        shard_data = item.get("shards")
        if shard_data:
            max_shard_in_item = max(shard["shard"] for shard in shard_data)
            if max_shard_in_item > max_shard:
                max_shard = max_shard_in_item
    return max_shard + 1


def get_shard_id(server_id, total_shards):
    """
    getShardId: function(t) {
        var e = parseInt(this.search);
        return parseInt(e.toString(2).slice(0, -22), 2) % t;
    }
    -where t is total shards of owo bot

    code from :- owobot.com/status, a random js script there.
    """
    e = int(server_id)
    """
    bin() returns binary of an int, 
    first two character is removed since it starts with prefix '0b'
    """
    binary_str = bin(e)[2:]
    if len(binary_str) > 22:
        sliced_binary_str = binary_str[:-22]
    else:
        sliced_binary_str = "0"  # this will never be executed.
    sliced_int = int(sliced_binary_str, 2)  # the ,2) makes it back into integer
    shard_id = (
        sliced_int % total_shards
    )  # the final modulus (i hope thats what its called) calc.
    return shard_id


# Calculate and print the shard ID


async def delaycheck(session, server_id):
    try:
        async with session.get(
            url, timeout=aiohttp.ClientTimeout(total=10)
        ) as response:
            response.raise_for_status()  # raises an HTTPError for bad responses (4xx, 5xx)
            json_data = await response.json()
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as e:
        print(f"An error occurred: {e}")
        return None

    if not json_data:
        return None

    total_shards = get_max_shards(json_data)
    if not total_shards:
        return None

    shard_id = get_shard_id(server_id, total_shards)

    for item in json_data:
        shard_data = item.get("shards")
        if shard_data:
            for i in shard_data:
                if i["shard"] == shard_id:
                    return i
    return None


async def is_shard_ready(session, server_id):
    shard = await delaycheck(session, server_id)
    return bool(shard and shard.get("status") == "ready")


# delaycheck(None, server_id)
