import sys

import click
import ollama

from ollama_manager.utils import convert_bytes, handle_interaction


def list_models() -> list[str] | None:
    model_names = []

    raw_models = ollama.list()
    if not raw_models:
        return None

    all_raw_models = raw_models["models"]

    max_length = max(len(model["name"]) for model in all_raw_models)

    for model in all_raw_models:
        model_names.append(
            f"{model['name']:<{max_length + 5}}{convert_bytes(model['size'])}"
        )

    return model_names


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
        selections = handle_interaction(models, multi_select=multi)
    else:
        print("❌ No models selected for deletion")
        sys.exit(0)

    if selections:
        for selection in selections:
            normalized_selection = selection.split()[0]
            ollama.delete(normalized_selection)
            print(f"🗑️ Deleted model: {normalized_selection}")
