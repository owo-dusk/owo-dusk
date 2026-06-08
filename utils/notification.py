import json

from utils.misc import is_termux, run_system_command


with open("config/misc.json", "r", encoding="utf-8") as config_file:
    misc_dict = json.load(config_file)


def notify(content, title):
    if misc_dict["hostMode"]:
        # Notification isn't supported in hosts and will trigger crash if unhandled
        return

    on_mobile = is_termux()

    if on_mobile:
        run_system_command(
            f"termux-notification -t '{title}' -c '{content}' --led-color '#a575ff' --priority 'high'",
            timeout=5,
            retry=True,
        )
    else:
        from plyer import notification

        notification.notify(
            title=str(title), message=str(content), app_icon="", timeout=15
        )
