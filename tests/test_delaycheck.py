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

import unittest

from utils.delaycheck import get_max_shards, get_shard_id


class DelaycheckTests(unittest.TestCase):
    def test_max_shards_counts_all_shards(self):
        payload = [
            {"shards": [{"shard": 0}, {"shard": 1}]},
            {"shards": [{"shard": 2}]},
        ]

        self.assertEqual(get_max_shards(payload), 3)

    def test_max_shards_ignores_empty_clusters(self):
        payload = [
            {"shards": []},
            {"shards": [{"shard": 4}]},
            {},
        ]

        self.assertEqual(get_max_shards(payload), 5)

    def test_max_shards_returns_zero_without_shards(self):
        self.assertEqual(get_max_shards([{}, {"shards": []}]), 0)

    def test_shard_id_matches_the_status_api(self):
        # Regression value for the shard math: 123456789012345678 maps to
        # shard 1176 when the status API reports 2560 shards.
        self.assertEqual(get_shard_id(123456789012345678, 2560), 1176)


if __name__ == "__main__":
    unittest.main()
