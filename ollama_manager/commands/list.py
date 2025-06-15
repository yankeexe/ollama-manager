import click
import ollama
from rich.console import Console
from rich.table import Table
from ollama_manager.utils import convert_bytes, humanized_relative_time


@click.command(name="list")
@click.option(
    "--sort",
    "-s",
    type=click.Choice(["name", "date", "size"]),
    default="name",
    help="Sort models by name, modified date, or size",
)
@click.option(
    "--order",
    "-o",
    type=click.Choice(["asc", "desc"]),
    default="asc",
    help="Sort order (ascending or descending)",
)
def list_ollama_models(sort, order):
    """
    List your ollama models
    """
    model_metadata = ollama.list()
    models = model_metadata.models

    # Sort models based on user preference
    if sort == "name":
        models.sort(key=lambda m: m.model, reverse=(order == "desc"))
    elif sort == "date":
        models.sort(key=lambda m: m.modified_at, reverse=(order == "desc"))
    elif sort == "size":
        models.sort(key=lambda m: m.size, reverse=(order == "desc"))

    console = Console()
    table = Table(title="Ollama Models")

    table.add_column("Model Name", style="bright_cyan")
    table.add_column("Modified Date", style="bright_green", justify="left")
    table.add_column("Size", style="bright_yellow", justify="left")

    # Add rows
    for model in models:
        model_name = model.model
        modified_date = humanized_relative_time(str(model.modified_at))
        size = convert_bytes(model.size)

        table.add_row(model_name, modified_date, size)

    console.print(table)
