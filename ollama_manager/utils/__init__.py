import sys

from simple_term_menu import TerminalMenu


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
