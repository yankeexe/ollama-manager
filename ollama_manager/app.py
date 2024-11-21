"""Entrypoint of the CLI"""

import click

from ollama_manager.commands import delete_model, pull_model


@click.group()
def cli():
    pass


cli.add_command(pull_model)
cli.add_command(delete_model)
