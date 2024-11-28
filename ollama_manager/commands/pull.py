import sys

import click
import ollama
import requests
from bs4 import BeautifulSoup

from ollama_manager.utils import get_session, handle_interaction, make_request


def list_remote_model_tags(model_name: str, session: requests.Session):
    response = make_request(
        session=session,
        url=f"https://ollama.com/library/{model_name}/tags",
    )
    soup = BeautifulSoup(response.text, "html.parser")

    # Find the span with the specific attribute
    # @NOTE: This might change with website updates.
    elements = soup.find_all(
        "div", class_="break-all font-medium text-gray-900 group-hover:underline"
    )

    if not elements:
        return None

    results = []
    for element in elements:
        # Get the title
        title = element.text.strip()

        # Find the next sibling div containing metadata
        # @NOTE: This might change with website updates.
        metadata_div = element.find_next(
            "div", class_="flex items-baseline space-x-1 text-[13px] text-neutral-500"
        )

        if metadata_div:
            # Extract metadata values
            metadata_text = metadata_div.text.strip()
            # Parse the metadata string
            # Example: "2887c3d03e74 • 2.5GB • 8 weeks ago"
            parts = metadata_text.split("•")
            hash_id = parts[0].strip()
            size = parts[1].strip()
            time_ago = parts[2].strip()

            results.append(
                {"title": title, "hash": hash_id, "size": size, "updated": time_ago}
            )

    return results


def list_remote_models(session: requests.Session) -> list[str] | None:
    response = make_request(session=session, url="https://ollama.com/search")

    soup = BeautifulSoup(response.text, "html.parser")
    # Find the span with the specific attribute
    # @NOTE: This might change with website updates.
    elements = soup.find_all("span", attrs={"x-test-search-response-title": True})
    if not elements:
        return None

    return [element.text.strip() for element in elements]


@click.command(name="pull")
def pull_model():
    """
    Pull models from Ollama library:

    https://ollama.dev/search
    """
    session = get_session()
    models = list_remote_models(session)
    if not models:
        print("❌ No models selected for download")
        sys.exit(0)

    model_selection = handle_interaction(
        models, title="📦 Select remote Ollama model\s:\n", multi_select=False
    )
    if model_selection:
        model_tags = list_remote_model_tags(
            model_name=model_selection[0], session=session
        )
        if not model_tags:
            print(f"❌ Failed fetching tags for: {model_selection}. Please try again.")
            sys.exit(1)

        max_length = max(len(f"{model_selection}:{tag['title']}") for tag in model_tags)

        model_name_with_tags = [
            f"{model_selection[0]}:{tag['title']:<{max_length + 5}}{tag['size']:<{max_length + 5}}{tag['updated']}"
            for tag in model_tags
        ]
        selected_model_with_tag = handle_interaction(
            model_name_with_tags, title="🔖 Select tag to download:\n"
        )
        if not selected_model_with_tag:
            print("No tag selected for the model")
            sys.exit(1)

        final_model = selected_model_with_tag[0].split()[0]
        print(f">>> Pulling model: {final_model}")
        response = ollama.pull(final_model, stream=True)
        for data in response:
            print(data)
