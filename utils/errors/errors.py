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

import re
import shutil
import threading
import traceback
from contextlib import contextmanager
from functools import wraps
from pathlib import Path

try:
    from rich.console import Console
    from rich.terminal_theme import MONOKAI

    from utils.errors import catbox

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    import utils.colors as clr


DISCORD_TOKEN_REGEX = re.compile(
    r"\b[A-Za-z0-9_-]{24,28}\.[A-Za-z0-9_-]{6,7}\.[A-Za-z0-9_-]{27,}\b"
)


class ConsolePrinter:
    def __init__(self):
        self.color_map = {
            "[bold yellow]": clr.COLORS.BOLD_YELLOW,
            "[magenta]": clr.COLORS.BOLD_MAGENTA,
            "[cyan]": clr.COLORS.BOLD_CYAN,
            "[dim]": clr.COLORS.RESET,
            "[bold red]": clr.COLORS.BOLD_RED,
            "[/bold yellow]": clr.COLORS.RESET,
            "[/magenta]": clr.COLORS.RESET,
            "[/cyan]": clr.COLORS.RESET,
            "[/dim]": clr.COLORS.RESET,
            "[/bold red]": clr.COLORS.RESET,
        }

    def _get_colored_string(self, text: str) -> str:
        for tag, color in self.color_map.items():
            text = text.replace(tag, color)

        # remove rich formatting
        text = text.replace("\\[", "[").replace("\\]", "]")
        return text

    # Either print text provided, or newline if none
    def print(self, text: str = "\n", *args, **kwargs):
        print(self._get_colored_string(text))


if RICH_AVAILABLE:
    console = Console(stderr=True, record=True, width=120)
else:
    console = ConsolePrinter()


def _log_exception(exc: Exception, resource_name: str) -> None:
    tb = traceback.extract_tb(exc.__traceback__)
    if tb:
        frame = tb[-1]
        location = f"{frame.filename}:{frame.lineno} (in {frame.name})"
    else:
        location = "Location Not Known"

    if isinstance(exc, KeyError):
        console.print(
            f"[bold yellow]\\[KeyError][/bold yellow] Missing expected data "
            f"key [cyan]{exc}[/cyan] in [magenta]'{resource_name}'[/magenta] "
            f"⇨ [dim]{location}[/dim]"
        )
    elif isinstance(exc, TypeError):
        console.print(
            f"[bold yellow]\\[TypeError][/bold yellow] Type mismatch in "
            f"[magenta]'{resource_name}'[/magenta] ⇨ [dim]{location}[/dim]: "
            f"{exc}"
        )
    else:
        console.print(
            f"[bold red]\\[Unexpected][/bold red] Failure in "
            f"[magenta]'{resource_name}'[/magenta] ⇨ [dim]{location}[/dim]"
        )
        if RICH_AVAILABLE:
            console.print_exception(
                show_locals=False,
                word_wrap=True,
                width=shutil.get_terminal_size().columns,
            )
        else:
            traceback.print_exc()

    if RICH_AVAILABLE:
        _upload_error_image()


def _redact_discord_tokens(text: str) -> str:
    """
    Redacts Discord token like texts
    """
    text = DISCORD_TOKEN_REGEX.sub("***DISCORD_TOKEN_REDACTED***", text)
    return text


def _upload_error_image():
    # Yes, the override is intended. Perhaps later we can use
    # a proper place for the errors so that previous errors are
    # only cleared after an proper interval
    filename = "error.svg"
    full_path = Path(filename).resolve()

    # Save Error as SVG and clear error
    svg_content = console.export_svg(
        title="OwO-Dusk Error Report", theme=MONOKAI, clear=True
    )
    svg_content = _redact_discord_tokens(svg_content)
    full_path.write_text(svg_content, encoding="utf-8")

    # Our functions could be used in async context as well
    # So we only lazily print url if upload is a success
    # If it fails then we will display a fallback text
    thread = threading.Thread(target=_log_error_image, daemon=True, args=(full_path,))
    thread.start()


def _log_error_image(path):
    url = catbox.upload_file(path)
    if url:
        console.print(
            "Oh no.. An error was detected but don't worry!\n"
            f"Error File: [magenta]'{url}'[/magenta] ⇨ [dim]{path}[/dim]\n"
            "Please share the catbox URL in OwO-Dusk Support server to recieve help if needed"
        )
    else:
        console.print(
            "Oh no.. An error was detected but don't worry!\n"
            f"Error File: [magenta]{path}[/magenta]\n"
            "Please share the image file in OwO-Dusk Support server from the path mentioned above to recieve help if needed"
        )


def suppress_and_log(resource_name: str = "Not mentioned"):
    def decorator(func):
        # Ensure doc strings works correctly
        # .. If i ever use any ;)
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                _log_exception(e, resource_name)
                return None

        return wrapper

    return decorator


@contextmanager
def suppress_and_log_block(resource_name: str = "Not mentioned"):
    try:
        yield
    except Exception as e:
        _log_exception(e, resource_name)
