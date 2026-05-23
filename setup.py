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
    "\033[1;32mwelcome to OwO-Dusk\nThis setup will guide you through with the setup of OwO-Dusk\nThankyou for your trust in OwO-Dusk\033[m"
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


"""while True:
    user_input = input("[?]Do you want help setting this up from scratch? (Y/N):-\n").lower()
    if user_input in ["y", "n"]:
        scratchSetup = True if user_input == "y" else False
        break
    else:
        print("[!]Please enter 'Y' or 'N'.")"""

scratchSetup = True
if scratchSetup:
    # print('[0]Alright, got it!')

    # ---INSTALL REQUIREMENTS--#
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
            # print("it may ask if you want to proceed with the installation...")
            # print("please type and enter \"Y\" for all such!")
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
    import discord
    import asyncio

    # ---EDIT TOKENS.TXT---#
    while True:
        edit_tokens = input(
            "\033[1;34mwould you like to edit tokens.txt?\n1) yes\n2) no\n:\033[m"
        ).lower()
        if edit_tokens in ["1", "2", "y", "n", "yes", "no"]:
            if edit_tokens in ["1", "y", "yes"]:
                print("\033[1;36m[0]attempting to edit tokens.txt\033[m")
                try:
                    """
                    open('filename.txt', x)
                    where if x is a then it adds while while preserving its content
                    and if its w it basically selects all text...? and removes it i guess.
                    -------------------------------
                    'r': Read (default mode)
                    'w': Write
                    'a': Append
                    'r+': Read and write
                    """
                    with open("tokens.txt", "w", encoding="utf-8") as t:
                        pass

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
                                    f"\033[1;36m[0] Received token for - {client.user.name} ({client.user.id})"
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
                                    await (
                                        client.close()
                                    )  # Close the client after successful login

                            await client.start(token)

                            # Return after the client is done running
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

                    while True:
                        token_count = input(
                            "\033[1;34m[0]how many accounts do you want run with owo-dusk? :\n\033[m"
                        )
                        try:
                            token_count = int(token_count)
                            break
                        except ValueError:
                            print("\033[1;31m[x]please enter valid integer!\033[m")
                        except Exception as e:
                            print(f"\033[1;31m[x]An error occured:-\n {e}\033[m")
                    for i in range(token_count):
                        while True:
                            print(f"\033[1;36m[0]token [{i + 1}/{token_count}]\033[m")
                            while True:
                                tokeninput = input(
                                    f"please enter your token for account #{i + 1} :\n\033[m"
                                )
                                if "." in tokeninput:
                                    if '"' in tokeninput:
                                        if tokeninput[0] == '"':
                                            tokeninput = tokeninput[1:]
                                        if tokeninput[-1] == '"':
                                            tokeninput = tokeninput[:-1]
                                        print(tokeninput)
                                    break
                                else:
                                    print("\033[1;31m[x]invalid token!")
                            while True:
                                channelinput = input(
                                    f"\033[1;34mplease enter channel id for account #{i + 1} :\n\033[m"
                                )
                                try:
                                    channelinput = int(channelinput)
                                    break
                                except ValueError:
                                    print(
                                        "\033[1;33m[!]please enter a valid integer for channelid\033[m"
                                    )
                                except Exception as e:
                                    print(
                                        f"\033[1;31m[x]error while attempting to retrieve channel id -\n{e}\033[m"
                                    )
                            # validtoken=False
                            try:
                                validtoken, validchannel = asyncio.run(
                                    validate_token(tokeninput, channelinput)
                                )
                            except Exception as e:
                                print(
                                    f"\033[1;31m[x] Error validating token for account #{i + 1}:\n{e}\033[m"
                                )
                            if validtoken:
                                if validchannel[0]:
                                    print(
                                        f"\033[1;36m[0]valid channel with name {validchannel[1]}\033[m"
                                    )
                                    break
                                else:
                                    print(
                                        "\033[1;31m[x]Failed to get channel id, please try again.\033[m"
                                    )
                        with open("tokens.txt", "a", encoding="utf-8") as t:
                            t.write(f"{tokeninput} {channelinput}\n")
                    print()
                    print()
                    print(
                        "\033[1;36m[0]Finished editing tokens.txt successfully!\033[m"
                    )
                    print(
                        "\033[1;32m[*]exiting code as basic installation is complete\nplease make sure to edit configs (settings, global_settings) from configs folder then\ntype `python uwu.py` to start the code\033[m"
                    )
                    break
                except Exception as e:
                    print(
                        f"\033[1;31m[x]error when attempting to edit tokens.txt - {e}\033[m"
                    )
            else:
                print(
                    "\033[1;32m[*]exiting code as basic installation is complete\nplease make sure to edit configuration files from config folder and `tokens.txt` file then\ntype `python uwu.py` to start the code\033[m"
                )
                break
        else:
            print("\033[1;33m[!]Please enter 1,2 only..\033[m")

print()
print(
    "\033[1;35mEchoQuill - Thank you for using owo-dusk, I hope you have a great day ahead!\nif there is any error then letme know through https://discord.gg/pyvKUh5mMU\033[m"
)
sys.exit(0)


"""else:
    y = input('''what would you like to do then?
1) install requirements.
2) check config.json
3) ''')"""
