import sys

import ollama
import requests
from simple_term_menu import TerminalMenu
from ollama._types import ListResponse

import datetime


def get_session() -> requests.Session:
    session = requests.Session()
    session.headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    return session


def list_models(only_names: bool = False) -> list[str] | None:
    model_names = []

    try:
        raw_models: ListResponse = ollama.list()
    except Exception:
        print("❌ Could not fetch models.\n>>> 🦙Is Ollama running?")
        sys.exit(1)

    if not raw_models:
        return None

    all_raw_models = raw_models.models

    max_length = max(len(model.model) for model in all_raw_models)

    for model in all_raw_models:
        if only_names:
            model_names.append(model.model)
            continue

        model_names.append(
            f"{model.model:<{max_length + 5}}{convert_bytes(model.size)}"
        )

    return model_names


def make_request(
    session: requests.Session, url: str, timeout: int = 5, params: dict[str, str] = None
):
    try:
        response = session.get(url, timeout=timeout, params=params)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to make request: {str(e)}")
        sys.exit(1)

    return response


def humanized_relative_time(datetime_str: str):
    """
    Converts a datetime string in ISO 8601 format to a human-readable relative time.

    Args:
        datetime_str: The datetime string in "YYYY-MM-DDTHH:MM:SS.mmmZ" format.

    Returns:
        A human-readable string representing the relative time, or the original
        datetime string if it cannot be parsed.
    """
    try:
        dt = datetime.datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
    except ValueError:
        return datetime_str  # Return original if parsing fails

    now = datetime.datetime.now(tz=datetime.timezone.utc)
    delta = now - dt

    if delta < datetime.timedelta(minutes=1):
        return "just now"
    elif delta < datetime.timedelta(hours=1):
        minutes = int(delta.total_seconds() // 60)
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    elif delta < datetime.timedelta(days=1):
        hours = int(delta.total_seconds() // 3600)
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif delta < datetime.timedelta(days=30):
        days = delta.days
        return f"{days} day{'s' if days > 1 else ''} ago"
    elif delta < datetime.timedelta(days=365):
        months = int(delta.days // 30)
        return f"{months} month{'s' if months > 1 else ''} ago"
    else:
        years = int(delta.days // 365)
        return f"{years} year{'s' if years > 1 else ''} ago"


def convert_bytes(bytes_value):
    """
    Convert bytes to human readable format (MB or GB).

    Args:
        bytes_value (int): Size in bytes to convert

    Returns:
        str: Formatted string with size in MB or GB (e.g. "1.50 MB" or "2.30 GB")
            Returns MB if size is less than 1 GB, otherwise returns GB
    """
    KB = 1024
    MB = KB * 1024
    GB = MB * 1024

    # Convert to MB first
    mb_value = bytes_value / MB

    if mb_value < 1024:  # Less than 1 GB
        return f"{mb_value:.2f} MB"
    else:  # 1 GB or more
        gb_value = bytes_value / GB
        return f"{gb_value:.2f} GB"


def handle_interaction(
    data: list, multi_select=False, title: str | None = None
) -> list[str]:
    """
    Display interactive menu on the terminal.
    """
    selections = []
    try:
        terminal_menu = TerminalMenu(
            data,
            multi_select=multi_select,
            show_multi_select_hint=multi_select,
            search_key=None,
            show_search_hint=True,
            title=title,
        )
        menu_entry_index: tuple | None = terminal_menu.show()

        # Check for None value when user presses `esc` or `ctrl + c`
        if menu_entry_index is None:
            raise KeyboardInterrupt

        if multi_select:
            # if more than one timezone is selected.
            for index in menu_entry_index:
                selections.append(data[index])
        else:
            selections.append(data[menu_entry_index])

    except KeyboardInterrupt:
        sys.exit()

    return selections
