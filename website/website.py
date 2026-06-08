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

import sqlite3
import random
import logging
import sys
import json
from flask import Flask, jsonify, render_template, request

from utils.timestamp import get_weekday

app = Flask(__name__)
website_logs = []
config_updated = None

# these will be updated
password = ""
version = ""


def merge_dicts(main, small):
    for key, value in small.items():
        if key in main and isinstance(main[key], dict) and isinstance(value, dict):
            merge_dicts(main[key], value)
        else:
            main[key] = value


def get_from_db(command):
    with sqlite3.connect("utils/data/db.sqlite") as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("PRAGMA journal_mode;")
        mode = cur.fetchone()[0]
        if mode.lower() != "wal":
            cur.execute("PRAGMA journal_mode=WAL;")

        cur.execute(command)

        item = cur.fetchall()
        return item


@app.route("/")
def home():
    return render_template("index.html", version=version)


@app.route("/api/console", methods=["GET"])
def get_console_logs():
    password = request.headers.get("password")
    if not password or password != password:
        return "Invalid Password", 401
    try:
        log_string = "\n".join(website_logs)
        return log_string
    except Exception as e:
        print(f"Error fetching logs: {e}")
        return jsonify(
            {"status": "error", "message": "An error occurred while fetching logs"}
        ), 500


@app.route("/api/fetch_gamble_data", methods=["GET"])
def fetch_gamble_data():
    password = request.headers.get("password")
    if not password or password != password:
        return "Invalid Password", 401
    try:
        # Fetch table data
        rows = get_from_db(
            "SELECT hour, wins, losses FROM gamble_winrate ORDER BY hour"
        )

        # Extract columns as lists
        win_data = [row["wins"] for row in rows]
        lose_data = [row["losses"] for row in rows]

        # Return Data
        return jsonify(
            {"status": "success", "win_data": win_data, "lose_data": lose_data}
        )

    except Exception as e:
        print(f"Error fetching gamble data: {e}")
        return jsonify(
            {
                "status": "error",
                "message": "An error occurred while fetching gamble data",
            }
        ), 500


@app.route("/api/fetch_cowoncy_data", methods=["GET"])
def fetch_cowoncy_data():
    password = request.headers.get("password")
    if not password or password != password:
        return "Invalid Password", 401

    try:
        rows = get_from_db(
            "SELECT user_id, hour, earnings FROM cowoncy_earnings ORDER BY hour"
        )
        user_data = {}
        for row in rows:
            user_id = row["user_id"]
            hour = row["hour"]
            earnings = row["earnings"]

            if user_id not in user_data:
                # Create dummy data
                user_data[user_id] = {i: 0 for i in range(24)}
            # populate
            user_data[user_id][hour] = earnings

        # Base data
        base_data = {"labels": [f"Hour {i}" for i in range(24)], "datasets": []}

        for user_id, hourly_data in user_data.items():
            color_hue = random.randint(0, 360)
            dataset = {
                "label": user_id,
                "data": [hourly_data[i] for i in range(24)],
                "borderColor": f"hsl({color_hue}, 100%, 50%)",
                "backgroundColor": f"hsl({color_hue}, 100%, 70%)",
                "fill": True,
                "tension": 0.4,
                "pointRadius": 0,
            }
            base_data["datasets"].append(dataset)

        rows = get_from_db("SELECT cowoncy, captchas FROM user_stats")
        total_cowoncy = sum(row["cowoncy"] for row in rows)
        # I understand this area is for cowoncy, but accessing thro here since lazy lol.
        total_captchas = sum(row["captchas"] for row in rows)

        return jsonify(
            {
                "status": "success",
                "data": base_data,
                "total_cash": total_cowoncy,
                "total_captchas": total_captchas,
            }
        ), 200

    except Exception as e:
        print(f"Error fetching cowoncy data: {e}")
        return jsonify(
            {
                "status": "error",
                "message": "An error occurred while fetching cowoncy data",
            }
        ), 500


@app.route("/api/fetch_cmd_data", methods=["GET"])
def fetch_cmd_data():
    password = request.headers.get("password")
    if not password or password != password:
        return "Invalid Password", 401
    try:
        rows = get_from_db("SELECT * FROM commands")

        filtered_rows = [row for row in rows if row["count"] != 0]

        command_names = [row["name"] for row in filtered_rows]
        count = [row["count"] for row in filtered_rows]

        for idx, item in enumerate(count):
            if item == 0:
                command_names.pop(idx)
                count.pop(idx)

        # Return Data
        return jsonify(
            {"status": "success", "command_names": command_names, "count": count}
        )

    except Exception as e:
        print(f"Error fetching command data: {e}")
        return jsonify(
            {
                "status": "error",
                "message": "An error occurred while fetching command data",
            }
        ), 500


@app.route("/api/fetch_weekly_runtime", methods=["GET"])
def fetch_weekly_runtime():
    password = request.headers.get("password")
    if not password or password != password:
        return "Invalid Password", 401
    try:
        # Fetch json data
        with open(
            "utils/data/weekly_runtime.json", "r", encoding="utf-8"
        ) as config_file:
            data_dict = json.load(config_file)

        runtime_data = [
            (val[1] - val[0]) / 60
            for val in data_dict.values()
            if isinstance(val, list)
        ]

        cur_hour = get_weekday()

        # Return Data
        return jsonify(
            {
                "status": "success",
                "runtime_data": runtime_data,
                "current_uptime": data_dict[cur_hour],
            }
        )

    except Exception as e:
        print(f"Error fetching weekly runtime: {e}")
        return jsonify(
            {
                "status": "error",
                "message": "An error occurred while fetching weekly runtime",
            }
        ), 500


def web_start(port, shouldHost, ver, paswd):
    # Set global variables with respective values
    global password, version
    password = paswd
    version = ver
    # Start the webserver
    flaskLog = logging.getLogger("werkzeug")
    flaskLog.disabled = True
    cli = sys.modules["flask.cli"]
    cli.show_server_banner = lambda *x: None
    app.run(
        debug=False,
        use_reloader=False,
        port=port,
        host="0.0.0.0" if shouldHost else "127.0.0.1",
    )


def website_append(content):
    global website_logs
    website_logs.append(content)

    if len(website_logs) > 300:
        website_logs.pop(0)
