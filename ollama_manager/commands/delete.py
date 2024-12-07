import sys

import click
import ollama

from ollama_manager.utils import handle_interaction, list_models


@click.command(name="rm")
@click.option(
    "--multi",
    "-m",
    help="Select multiple models at once",
    type=bool,
    default=False,
    is_flag=True,
)
@click.option(
    "--yes",
    "-y",
    help="Skip confirmation prompt for deletion",
    type=bool,
    default=False,
    is_flag=True,
)
def delete_model(multi: bool, yes: bool):
    """
    Deletes the selected model/s
    """
    models = list_models()
    if models:
        selections = handle_interaction(
            models, multi_select=multi, title="🗑️ Select model/s to delete:\n"
        )
    else:
        print("❌ No models selected for deletion")
        sys.exit(0)

    if selections:
        for selection in selections:
            normalized_selection = selection.split()[0]
            if not yes:
                confirm = input(
                    f"Are you sure you want to delete '\033[91m{normalized_selection}\033[0m'? \n[y(yes) | n(no)] "
                )

                if confirm.strip() in ("yes", "y"):
                    ollama.delete(normalized_selection)
                else:
                    print("❌ Exited delete mode.")
                    sys.exit(0)
            else:
                ollama.delete(normalized_selection)
            print(f"🗑️ Deleted model: {normalized_selection}")
