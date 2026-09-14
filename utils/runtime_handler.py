import json
import os
import threading
import time

import utils.timestamp as utils
from utils.colors import COLORS
from utils.errors import suppress_and_log

path = "utils/data/weekly_runtime.json"

DEFAULT_WEEKLY_RUNTIME = {
    "0": [0, 0],
    "1": [0, 0],
    "2": [0, 0],
    "3": [0, 0],
    "4": [0, 0],
    "5": [0, 0],
    "6": [0, 0],
    "last_checked": 0,
}


def _write_weekly_runtime(weekly_runtime_dict, path):
    # write to a temp file then swap it in so a crash/kill mid-write
    # can't leave the real file empty/half-written
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(weekly_runtime_dict, f, indent=4)
    os.replace(tmp_path, path)


def load_weekly_runtime(path="utils/data/weekly_runtime.json") -> dict:
    try:
        with open(path, "r", encoding="utf-8") as config_file:
            return json.load(config_file)
    except (json.JSONDecodeError, FileNotFoundError, OSError):
        print(
        f"{COLORS.BOLD_YELLOW}Weekly runtime data file is missing or corrupted — recreating with default values.{COLORS.RESET}"
        )
        weekly_runtime_dict = {
            k: (v.copy() if isinstance(v, list) else v)
            for k, v in DEFAULT_WEEKLY_RUNTIME.items()
        }
        _write_weekly_runtime(weekly_runtime_dict, path)
        return weekly_runtime_dict


@suppress_and_log("Weekly Runtime Updater")
def handle_weekly_runtime(path="utils/data/weekly_runtime.json"):
    while True:
        weekly_runtime_dict = load_weekly_runtime(path)
        weekday = utils.get_weekday()

        if weekly_runtime_dict[weekday][0] == 0:
            weekly_runtime_dict[weekday][0], weekly_runtime_dict[weekday][1] = (
                time.time(),
                time.time(),
            )
        else:
            weekly_runtime_dict[weekday][1] = time.time()

        try: # bcz widnows can refuse the replace if another process holds the file open
            _write_weekly_runtime(weekly_runtime_dict, path)
        except OSError:
            print(
                f"{COLORS.BOLD_YELLOW}Weekly runtime file is locked — retrying on next tick.{COLORS.RESET}"
            )
        # update every 15 seconds
        time.sleep(15)


@suppress_and_log("Weekly Runtime Update Starter")
def start_runtime_loop(path="utils/data/weekly_runtime.json"):
    weekly_runtime_dict = load_weekly_runtime(path)

    now = time.time()
    last_checked = weekly_runtime_dict.get("last_checked", 0)

    if now - last_checked > 604800:  # 604800 -> seconds in a week
        for day in map(str, range(7)):
            weekly_runtime_dict[day] = [0, 0]

    weekly_runtime_dict["last_checked"] = now

    try: # bcz widnows can refuse the replace if another process holds the file open
        _write_weekly_runtime(weekly_runtime_dict, path)
    except OSError:
        print(
            f"{COLORS.BOLD_YELLOW}Weekly runtime file is locked — retrying on next tick.{COLORS.RESET}"
        )

    loop_thread = threading.Thread(target=handle_weekly_runtime, daemon=True)
    loop_thread.start()
