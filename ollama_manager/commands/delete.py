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
def delete_model(multi: bool):
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
            ollama.delete(normalized_selection)
            print(f"🗑️ Deleted model: {normalized_selection}")
