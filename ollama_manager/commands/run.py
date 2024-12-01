import os
import subprocess
import sys
from pathlib import Path

import click

from ollama_manager.utils import handle_interaction, list_models

try:
    import streamlit  # noqa F401
except ImportError:
    print(
        """
⚠️ Running models using ollama-manager is an optional feature.

To use it install the optional dependency:

>> pip install ollama-manager[ui]
"""
    )
    sys.exit(1)


@click.command(name="run")
def run_model():
    """
    [WIP] Run Ollama models in a streamlit UI.

    ⚠️ Only text models are supported for now.
    """

    models = list_models()
    if models:
        selection = handle_interaction(
            models, title="⚡️ Select model to run:\n", multi_select=False
        )
    else:
        print("❌ No models selected for running with Streamlit UI")
        sys.exit(0)

    if selection:
        normalized_selection = selection[0].split()[0]
        script_path = (
            Path(os.path.abspath(__file__)).parent.parent / "ui" / "text_chat.py"
        )
        command = ["streamlit", "run", str(script_path), "--", normalized_selection]

        try:
            process = subprocess.Popen(command)
            process.wait()
        except Exception as e:
            print(f"Error running Streamlit app: {e}")
