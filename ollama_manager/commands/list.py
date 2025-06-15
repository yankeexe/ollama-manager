import click
import ollama
from rich.console import Console
from rich.table import Table
from ollama_manager.utils import convert_bytes, humanized_relative_time


@click.command(name="list")
def list_ollama_models():
    """
    List your ollama models
    """
    model_metadata = ollama.list()

    console = Console()
    table = Table(title="Ollama Models")

    table.add_column("Model Name", style="bright_cyan")
    table.add_column("Modified Date", style="bright_green", justify="left")
    table.add_column("Size", style="bright_yellow", justify="left")

    # Add rows
    for model in model_metadata.models:
        model_name = model.model
        modified_date = humanized_relative_time(str(model.modified_at))
        size = convert_bytes(model.size)

        table.add_row(model_name, modified_date, size)

    console.print(table)
