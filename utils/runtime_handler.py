import json
import os
import tempfile
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
    target_dir = os.path.dirname(path)
    
    # This temporary file is uniquely named, preventing race conditions making the file be unavailable.
    tmp_file = tempfile.NamedTemporaryFile(
        mode="w", 
        encoding="utf-8", 
        dir=target_dir, 
        delete=False
    )
    tmp_path = tmp_file.name
    
    try:
        # Write dummy to temporary file
        json.dump(weekly_runtime_dict, tmp_file, indent=4)
        # Windows requires the file to be closed before replace
        tmp_file.close()
        
        os.replace(tmp_path, path)
    finally:
        # Deletion of temporary file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def load_weekly_runtime(path="utils/data/weekly_runtime.json") -> dict:
    try:
        with open(path, "r", encoding="utf-8") as config_file:
            return json.load(config_file)
    except (json.JSONDecodeError, FileNotFoundError, OSError):
        print(
        f"{COLORS.BOLD_YELLOW}Weekly runtime data file is missing or corrupted, recreating with default values.{COLORS.RESET}"
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

        try: # bcz windows can refuse the replace if another process holds the file open
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

    try: # bcz windows can refuse the replace if another process holds the file open
        _write_weekly_runtime(weekly_runtime_dict, path)
    except OSError:
        print(
            f"{COLORS.BOLD_YELLOW}Weekly runtime file is locked — retrying on next tick.{COLORS.RESET}"
        )

    loop_thread = threading.Thread(target=handle_weekly_runtime, daemon=True)
    loop_thread.start()
