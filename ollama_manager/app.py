"""Entrypoint of the CLI"""

import click

from ollama_manager.commands.delete import delete_model
from ollama_manager.commands.pull import pull_model
from ollama_manager.commands.run import run_model


@click.group()
def cli():
    pass


cli.add_command(pull_model)
cli.add_command(delete_model)
cli.add_command(run_model)
