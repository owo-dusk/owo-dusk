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

import os
import sys
import subprocess
import tomllib

try:
    os.system("cls") if os.name == "nt" else os.system("clear")
except Exception:
    pass
print(
    "\033[1;32mWelcome to OwO-Dusk\nThis setup will guide you through with the setup of OwO-Dusk\nThank you for your trust in OwO-Dusk <3\033[m"
)


def load_json_dict(file_path="config/captcha.toml"):
    with open(file_path, "rb") as config_file:
        return tomllib.load(config_file)


cap_cnf_dict = load_json_dict()


def is_termux():
    termux_prefix = os.environ.get("PREFIX")
    termux_home = os.environ.get("HOME")

    if termux_prefix and "com.termux" in termux_prefix:
        return True
    elif termux_home and "com.termux" in termux_home:
        return True
    else:
        return os.path.isdir("/data/data/com.termux")


# initial choice for setup type
while True:
    choice = input(
        "\033[1;34mWhat would you like to do?\n1) Setup from scratch (installs modules + clears tokens.txt)\n2) Add token to existing setup (retains existing tokens)\n:\033[m"
    ).strip()
    if choice in ["1", "2"]:
        break
    else:
        print("\033[1;33m[!]Please enter 1 or 2 only.\033[m")

scratchSetup = choice == "1"

if scratchSetup:
    # ---INSTALL REQUIREMENTS---#
    print("\033[1;36m[0]attempting to install requirements.txt\033[m")
    try:
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
            )
        except Exception:
            if is_termux():
                print(
                    "\033[1;36m[0]attempting to retry installing requirements.txt, after ensuring pkgs are uptodate\033[m"
                )
                subprocess.check_call(["pkg", "update", "-y"])
                subprocess.check_call(["pkg", "upgrade", "-y"])
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
                )
        print(
            "\033[1;36m[0]Installed modules from requirements.txt successfully!\033[m"
        )
        print("\033[1;36m[0]attempting to install numpy and pil\033[m")
        if is_termux():
            # Termux
            print("\033[1;36m[0]installing for termux...\033[m")
            print()
            print(
                "\033[1;36m[info]We are going to be making use of termux's version of numpy and pil as normal ones won't work with termux.\033[m"
            )
            print()

            """Numpy Installation"""
            print("\033[1;36m[0]Attempting to install numpy\033[m")
            try:
                subprocess.check_call(["pkg", "install", "python-numpy", "-y"])
                print("\033[1;36m[0]installed numpy successfully!\033[m")
            except Exception as e:
                print(f"\033[1;31m[x]error when trying to install numpy:-\n {e}\033[m")

            """PILL Installation"""
            print("\033[1;36m[0]Attempting to install PIL\033[m")
            try:
                subprocess.check_call(["pkg", "install", "python-pillow", "-y"])
                print("\033[1;36m[0]installed PIL successfully!\033[m")
            except Exception as e:
                print(f"\033[1;31m[x]error when trying to install PIL:-\n {e}\033[m")

            """Termux-api Installation"""
            print("\033[1;36m[0]Attempting to install termux-api...\033[m")
            try:
                subprocess.check_call(["pkg", "install", "termux-api", "-y"])
                print("\033[1;36m[0]installed termux-api successfully!\033[m")
            except Exception as e:
                print(
                    f"\033[1;31m[x]error when trying to install termux-api:-\n {e}\033[m"
                )
            if cap_cnf_dict["image_solver"]["enabled"]:
                print("\033[1;36m[0]Attempting to install onnxruntime...\033[m")
                try:
                    subprocess.check_call(
                        ["pkg", "install", "python-onnxruntime", "-y"]
                    )
                    print("\033[1;36m[0]installed onnxruntime successfully!\033[m")
                except Exception as e:
                    print(
                        f"\033[1;31m[x]error when trying to install Onnxruntime:-\n {e}\033[m"
                    )

        else:
            print("\033[1;36minstalling normally...\033[m")
            to_install = [
                sys.executable,
                "-m",
                "pip",
                "install",
                "numpy",
                "pillow",
                "playsound3",
                "plyer",
                "psutil",
            ]
            if cap_cnf_dict["image_solver"]["enabled"]:
                to_install.append("onnxruntime")

            try:
                subprocess.check_call(to_install)
                print("\033[1;36m[0]Installed numpy and PIL successfully!\033[m")
            except Exception as e:
                print(
                    f"\033[1;31m[x]Error when trying to install numpy and PIL: {e}\033[m"
                )

    except Exception as e:
        print(f"\033[1;31m[x]error when trying to install requirements:-\n {e}\033[m")

    print()
    print()

''' 
in option 1, discord is installed by the pip calls above.
in option 2, it is assumed to already be installed from a previous scratch setup, and if not, the user will be prompted to do a scratch setup to get it installed before adding tokens.
'''
try:
    import discord
    import asyncio
except ImportError:
    print(
        "\033[1;31m[x]Required modules are not installed.\nPlease run setup again and choose option 1 (setup from scratch) to install them first.\033[m"
    )
    sys.exit(1)

# shared collection function for both options, with internal async token validation to avoid event loop issues with discord.py-self
async def collect_tokens(token_count):
    async def validate_token(token, channelinput):
        try:
            client = discord.Client()
            result = {
                "valid": False,
                "channel_found": False,
                "channel": None,
            }

            @client.event
            async def on_ready():
                print(
                    f"\033[1;32m[✓] Received token for - {client.user.name} ({client.user.id})\033[m"
                )
                try:
                    channel = client.get_channel(channelinput)
                    result["valid"] = True
                    if channel:
                        result["channel_found"] = True
                        result["channel"] = channel
                except Exception as e:
                    print(
                        f"[x] An error occurred while checking the channel:\n{e}\033[m"
                    )
                finally:
                    await asyncio.sleep(0.1)
                    await client.close()

            await client.start(token)

            return result["valid"], (
                result["channel_found"],
                result["channel"],
            )

        except discord.LoginFailure:
            print(
                "\033[1;31m[x] Invalid token provided. Please check and try again.\033[m"
            )
            return False, (False, None)
        except Exception as e:
            print(f"\033[1;31m[x] An error occurred:\n{e}")
            return False, (False, None)

    collected = []
    for i in range(token_count):
        # Retry loop for the same account — keeps i fixed until entry is successful
        while True:
            print(f"\033[1;36m[0]token [{i + 1}/{token_count}]\033[m")

            # Separate loop for token input
            while True:
                tokeninput = input(
                    f"\033[1;34mplease enter your token for account #{i + 1}\n(guide on how to get your token: https://gist.github.com/nil-san/8ab7ff588412ee84a0391d493eaeaf43) :\n\033[m"
                ).strip().strip('"').strip("'")
                if "." in tokeninput:
                    break
                else:
                    print("\033[1;31m[x]invalid token!")

            # Separate loop for channelid + validation
            while True:
                channelinput = input(
                    f"\033[1;34mplease enter channel id for account #{i + 1} :\n\033[m"
                ).strip().strip('"').strip("'")
                try:
                    channelinput = int(channelinput)
                except ValueError:
                    print("\033[1;33m[!]please enter a valid integer for channelid\033[m")
                    continue
                except Exception as e:
                    print(f"\033[1;31m[x]error while attempting to retrieve channel id -\n{e}\033[m")
                    continue

                validtoken = False
                validchannel = (False, None)
                try:
                    validtoken, validchannel = await validate_token(tokeninput, channelinput)
                except Exception as e:
                    print(
                        f"\033[1;31m[x] Error validating token for account #{i + 1}:\n{e}\033[m"
                    )

                if not validtoken:
                    # Token itself is invalid — break channel loop to re-ask token
                    break
                if validchannel[0]:
                    print(
                        f"\033[1;32m[✓]valid channel with name {validchannel[1]}\033[m"
                    )
                    break
                else:
                    # Token fine but channel not found — re ask channel only
                    print(
                        "\033[1;31m[x]Failed to get channel id, please try again.\033[m"
                    )

            if validtoken and validchannel[0]:
                # Both valid — break retry loop and move to next account
                collected.append((tokeninput, channelinput))
                break
            else:
                print("\033[1;31m[x]Invalid token, please re-enter details for this account.\033[m")
                # Loop back to retry the same account

    return collected


# ---EDIT TOKENS.TXT---#
try:
    if scratchSetup:
        # Warn and confirm before wiping
        print(
            "\033[1;31m[!]Warning: This will clear everything currently in tokens.txt.\033[m"
        )
        while True:
            confirm = input(
                "\033[1;34mAre you sure you want to continue?\n1) yes\n2) no\n:\033[m"
            ).lower()
            if confirm in ["1", "y", "yes"]:
                break
            elif confirm in ["2", "n", "no"]:
                print("\033[1;36m[0]Cancelled. tokens.txt was not modified.\033[m")
                sys.exit(0)
            else:
                print("\033[1;33m[!]Please enter 1 or 2 only.\033[m")

        # Wipe tokens.txt
        with open("tokens.txt", "w", encoding="utf-8") as t:
            pass
        print("\033[1;36m[0]tokens.txt cleared.\033[m")
    else:
        print("\033[1;36m[0]Adding tokens to existing tokens.txt.\033[m")

    # Safeguard for 0 and negative account count
    while True:
        token_count = input(
            "\033[1;34m[0]how many accounts do you want to add? :\n\033[m"
        )
        try:
            token_count = int(token_count)
            if token_count <= 0:
                print("\033[1;31m[x]please enter at least 1 account!\033[m")
                continue
            break
        except ValueError:
            print("\033[1;31m[x]please enter valid integer!\033[m")
        except Exception as e:
            print(f"\033[1;31m[x]An error occured:-\n {e}\033[m")

    collected_tokens = asyncio.run(collect_tokens(token_count))

    # Read existing tokens to check for duplicates
    existing_tokens = set()
    try:
        with open("tokens.txt", "r", encoding="utf-8") as t:
            for line in t:
                line = line.strip()
                if line:
                    existing_tokens.add(line.split()[0])
    except FileNotFoundError:
        pass

    duplicates = 0
    for tokeninput, channelinput in collected_tokens:
        if tokeninput in existing_tokens:
            print(f"\033[1;33m[!]Token for account already exists in tokens.txt, skipping.\033[m")
            duplicates += 1
            continue
        with open("tokens.txt", "a", encoding="utf-8") as t:
            t.write(f"{tokeninput} {channelinput}\n")

    written = len(collected_tokens) - duplicates

    print()
    print()
    print(f"\033[1;36m[0]Finished! {written}/{len(collected_tokens)} account(s) written to tokens.txt.\033[m")
    print(
        "\033[1;32m[*]exiting code as basic installation is complete\nplease make sure to edit configs (settings, global_settings) from configs folder then\ntype `python uwu.py` to start the code\033[m"
    )

except Exception as e:
    print(f"\033[1;31m[x]error when attempting to edit tokens.txt - {e}\033[m")

print()
print(
    "\033[1;35mEchoQuill - Thank you for using owo-dusk, I hope you have a great day ahead!\nif there is any error then letme know through https://discord.gg/pyvKUh5mMU\033[m"
)
sys.exit(0)