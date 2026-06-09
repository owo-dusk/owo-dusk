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

from utils.colors import COLORS

from utils.system import (
    clear,
    install_package,
    install_termux_package,
    is_termux,
)

try:
    clear()
except Exception:
    pass


def load_json_dict(file_path="config/captcha.toml"):
    with open(file_path, "rb") as config_file:
        return tomllib.load(config_file)


cap_cnf_dict = load_json_dict()

print(
    f"{COLORS.BOLD_GREEN}Welcome to OwO-Dusk\nThis setup will guide you through with the setup of OwO-Dusk\nThank you for your trust in OwO-Dusk <3{COLORS.RESET}"
)

# initial choice for setup type
while True:
    choice = input(
        f"{COLORS.BOLD_BLUE}What would you like to do?\n1) Setup from scratch (installs modules + clears tokens.txt)\n2) Add token to existing setup (retains existing tokens)\n:{COLORS.RESET}"
    ).strip()
    if choice in ["1", "2"]:
        break
    else:
        print(f"{COLORS.BOLD_YELLOW}[!]Please enter 1 or 2 only.{COLORS.RESET}")

scratchSetup = choice == "1"

if scratchSetup:
    # ---INSTALL REQUIREMENTS--- #
    print(f"{COLORS.BOLD_CYAN}[0]attempting to install requirements.txt{COLORS.RESET}")
    try:
        try:
            install_package("-r", "requirements.txt")
        except Exception:
            if is_termux():
                print(
                    f"{COLORS.BOLD_CYAN}[0]attempting to retry installing requirements.txt, after ensuring pkgs are uptodate{COLORS.RESET}"
                )
                subprocess.check_call(["pkg", "update", "-y"])
                subprocess.check_call(["pkg", "upgrade", "-y"])
                install_package("-r", "requirements.txt")
            else:
                raise
        print(
            f"{COLORS.BOLD_CYAN}[0]Installed modules from requirements.txt successfully!{COLORS.RESET}"
        )
        print(f"{COLORS.BOLD_CYAN}[0]attempting to install numpy and pil{COLORS.RESET}")
        if is_termux():
            # Termux
            print(f"{COLORS.BOLD_CYAN}[0]installing for termux...{COLORS.RESET}")
            print()
            print(
                f"{COLORS.BOLD_CYAN}[info]We are going to be making use of termux's version of numpy and pil as normal ones won't work with termux.{COLORS.RESET}"
            )
            print()

            # Numpy Installation
            if not install_termux_package("python-numpy", "numpy"):
                raise RuntimeError("Failed to install numpy")

            # PIL Installation
            if not install_termux_package("python-pillow", "PIL"):
                raise RuntimeError("Failed to install PIL")

            # Termux-api installation
            if not install_termux_package("termux-api"):
                raise RuntimeError("Failed to install termux-api")

            if cap_cnf_dict["image_solver"]["enabled"]:
                if not install_termux_package("python-onnxruntime", "onnxruntime"):
                    raise RuntimeError("Failed to install onnxruntime")

        else:
            print(f"{COLORS.BOLD_CYAN}installing normally...{COLORS.RESET}")
            packages = [
                "numpy",
                "pillow",
                "playsound3",
                "plyer",
                "psutil",
            ]
            if cap_cnf_dict["image_solver"]["enabled"]:
                packages.append("onnxruntime")

            try:
                install_package(*packages)
                print(
                    f"{COLORS.BOLD_CYAN}[0]Installed numpy, PIL and dependencies successfully!{COLORS.RESET}"
                )
            except Exception as e:
                print(
                    f"{COLORS.BOLD_RED}[x]Error when trying to install numpy and PIL: {e}{COLORS.RESET}"
                )

    except Exception as e:
        print(
            f"{COLORS.BOLD_RED}[x]error when trying to install requirements:-\n {e}{COLORS.RESET}"
        )

    print()
    print()

try:
    import discord
    import asyncio
except ImportError:
    print(
        f"{COLORS.BOLD_RED}[x]Required modules are not installed.\nPlease run setup again and choose option 1 (setup from scratch) to install them first.{COLORS.RESET}"
    )
    sys.exit(1)


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
                    f"{COLORS.BOLD_GREEN}[✓] Received token for - {client.user.name} ({client.user.id}){COLORS.RESET}"
                )
                try:
                    channel = client.get_channel(channelinput)
                    result["valid"] = True
                    if channel:
                        result["channel_found"] = True
                        result["channel"] = channel
                except Exception as e:
                    print(
                        f"{COLORS.BOLD_RED}[x] An error occurred while checking the channel:\n{e}{COLORS.RESET}"
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
                f"{COLORS.BOLD_RED}[x] Invalid token provided. Please check and try again.{COLORS.RESET}"
            )
            return False, (False, None)
        except Exception as e:
            print(f"{COLORS.BOLD_RED}[x] An error occurred:\n{e}{COLORS.RESET}")
            return False, (False, None)

    collected = []
    for i in range(token_count):
        while True:
            print(f"{COLORS.BOLD_CYAN}[0]token [{i + 1}/{token_count}]{COLORS.RESET}")

            while True:
                tokeninput = (
                    input(
                        f"{COLORS.BOLD_BLUE}please enter your token for account #{i + 1}\n(guide on how to get your token: https://gist.github.com/nil-san/8ab7ff588412ee84a0391d493eaeaf43) :\n{COLORS.RESET}"
                    )
                    .strip()
                    .strip('"')
                    .strip("'")
                )
                if "." in tokeninput:
                    break
                else:
                    print(f"{COLORS.BOLD_RED}[x]invalid token!{COLORS.RESET}")

            while True:
                channelinput = (
                    input(
                        f"{COLORS.BOLD_BLUE}please enter channel id for account #{i + 1} :\n{COLORS.RESET}"
                    )
                    .strip()
                    .strip('"')
                    .strip("'")
                )
                try:
                    channelinput = int(channelinput)
                except ValueError:
                    print(
                        f"{COLORS.BOLD_YELLOW}[!]please enter a valid integer for channelid{COLORS.RESET}"
                    )
                    continue
                except Exception as e:
                    print(
                        f"{COLORS.BOLD_RED}[x]error while attempting to retrieve channel id -\n{e}{COLORS.RESET}"
                    )
                    continue

                validtoken = False
                validchannel = (False, None)
                try:
                    validtoken, validchannel = await validate_token(
                        tokeninput, channelinput
                    )
                except Exception as e:
                    print(
                        f"{COLORS.BOLD_RED}[x] Error validating token for account #{i + 1}:\n{e}{COLORS.RESET}"
                    )

                if not validtoken:
                    break
                if validchannel[0]:
                    print(
                        f"{COLORS.BOLD_GREEN}[✓]valid channel with name {validchannel[1]}{COLORS.RESET}"
                    )
                    break
                else:
                    print(
                        f"{COLORS.BOLD_RED}[x]Failed to get channel id, please try again.{COLORS.RESET}"
                    )

            if validtoken and validchannel[0]:
                collected.append((tokeninput, channelinput))
                break
            else:
                print(
                    f"{COLORS.BOLD_RED}[x]Invalid token, please re-enter details for this account.{COLORS.RESET}"
                )

    return collected


# ---EDIT TOKENS.TXT--- #
try:
    if scratchSetup:
        # Warn and confirm before wiping
        print(
            f"{COLORS.BOLD_RED}[!]Warning: This will clear everything currently in tokens.txt.{COLORS.RESET}"
        )
        while True:
            confirm = input(
                f"{COLORS.BOLD_BLUE}Are you sure you want to continue?\n1) yes\n2) no\n:{COLORS.RESET}"
            ).lower()
            if confirm in ["1", "y", "yes"]:
                break
            elif confirm in ["2", "n", "no"]:
                print(
                    f"{COLORS.BOLD_CYAN}[0]Cancelled. tokens.txt was not modified.{COLORS.RESET}"
                )
                sys.exit(0)
            else:
                print(f"{COLORS.BOLD_YELLOW}[!]Please enter 1 or 2 only.{COLORS.RESET}")

        # Wipe tokens.txt
        with open("tokens.txt", "w", encoding="utf-8") as t:
            pass
        print(f"{COLORS.BOLD_CYAN}[0]tokens.txt cleared.{COLORS.RESET}")
    else:
        print(
            f"{COLORS.BOLD_CYAN}[0]Adding tokens to existing tokens.txt.{COLORS.RESET}"
        )

    while True:
        token_count = input(
            f"{COLORS.BOLD_BLUE}[0]how many accounts do you want to add? :\n{COLORS.RESET}"
        )
        try:
            token_count = int(token_count)
            if token_count <= 0:
                print(
                    f"{COLORS.BOLD_RED}[x]please enter at least 1 account!{COLORS.RESET}"
                )
                continue
            break
        except ValueError:
            print(f"{COLORS.BOLD_RED}[x]please enter valid integer!{COLORS.RESET}")
        except Exception as e:
            print(f"{COLORS.BOLD_RED}[x]An error occurred:-\n {e}{COLORS.RESET}")

    collected_tokens = asyncio.run(collect_tokens(token_count))

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
            print(
                f"{COLORS.BOLD_YELLOW}[!]Token for account already exists in tokens.txt, skipping.{COLORS.RESET}"
            )
            duplicates += 1
            continue
        with open("tokens.txt", "a", encoding="utf-8") as t:
            t.write(f"{tokeninput} {channelinput}\n")

    written = len(collected_tokens) - duplicates

    print("\n\n")
    print(
        f"{COLORS.BOLD_CYAN}[0]Finished! {written}/{len(collected_tokens)} account(s) written to tokens.txt.{COLORS.RESET}"
    )
    print(
        f"{COLORS.BOLD_GREEN}[*]exiting code as basic installation is complete\nplease make sure to edit configs (settings, global_settings) from configs folder then\ntype `python uwu.py` to start the code{COLORS.RESET}"
    )

except Exception as e:
    print(
        f"{COLORS.BOLD_RED}[x]error when attempting to edit tokens.txt - {e}{COLORS.RESET}"
    )

print()
print(
    f"{COLORS.BOLD_MAGENTA}EchoQuill - Thank you for using owo-dusk, I hope you have a great day ahead!\nif there is any error then let me know through https://discord.gg/pyvKUh5mMU{COLORS.RESET}"
)
sys.exit(0)
