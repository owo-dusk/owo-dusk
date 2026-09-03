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

import tkinter as tk
from queue import Queue

from utils.errors import suppress_and_log
from utils.loader import global_settings_dict

popup_queue = Queue()

# Task: Maybe better to handle termux popup directly from here
# instead of handling it externally making there be a need
# to control imports


@suppress_and_log("Popup Queue")
def popup_main_loop():
    root = tk.Tk()
    root.withdraw()

    def check_queue():
        if popup_queue.qsize() != 0:
            # Should not be empty as size not 0
            msg, username, channelname, captchatype = popup_queue.get_nowait()
        else:
            root.after(100, check_queue)
            return

        popup = tk.Toplevel(root)
        popup.configure(bg="#000000")
        popup.title("OwO-dusk - Notifs")

        try:
            icon_path = "website/static/imgs/logo.png"
            icon = tk.PhotoImage(file=icon_path)
            popup.iconphoto(True, icon)
        except Exception as e:
            print(f"Failed to load icon: {e}")

        # Fetch screen width and height
        screen_width = popup.winfo_screenwidth()
        screen_height = popup.winfo_screenheight()

        popup_width = min(500, int(screen_width * 0.8))
        popup_height = min(300, int(screen_height * 0.8))

        x_position = (screen_width - popup_width) // 2
        y_position = (screen_height - popup_height) // 2

        popup.geometry(f"{popup_width}x{popup_height}+{x_position}+{y_position}")

        label_text = msg.format(
            username=username, channelname=channelname, captchatype=captchatype
        )

        label = tk.Label(
            popup,
            text=label_text,
            wraplength=popup_width - 40,
            justify="left",
            padx=20,
            pady=20,
            bg="#000000",
            fg="#be7dff",
        )
        label.pack(fill="both", expand=True)

        button = tk.Button(popup, text="OK", command=popup.destroy)
        button.pack(pady=10)

        # Directly calling these functions may cause issues
        # popup.after helps ensure that doesn't happen
        popup.after(0, popup.lift)
        popup.after(0, popup.focus_force)

        # Restart queue check if window destroyed
        popup.bind("<Destroy>", lambda e: root.after(100, check_queue))

    check_queue()
    root.mainloop()


@suppress_and_log("Adding to Popup queue")
def add_popup_queue(username, channel_name, captcha_type=None):
    popup_queue.put(
        (
            (
                global_settings_dict.captcha.toastOrPopup.captchaContent
                if captcha_type != "Ban"
                else global_settings_dict.captcha.toastOrPopup.bannedContent
            ),
            username,
            channel_name,
            captcha_type,
        )
    )
