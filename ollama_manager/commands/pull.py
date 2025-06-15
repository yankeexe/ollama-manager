import re
import sys

import click
import httpx
import ollama
from bs4 import BeautifulSoup, SoupStrainer
from rich.console import Console

from ollama_manager.utils import coro, handle_interaction, humanized_relative_time


def extract_quantization(text):
    """
    Extracts the quantization information from a model filename.

    Args:
        text: The model filename string.

    Returns:
        The quantization string (e.g., "Q2_K", "IQ4_K") or None if not found.
    """
    match = re.search(r"IQ\w+\.", text)  # Check for "IQ" first
    if match:
        return match.group(0)[:-1]
    match = re.search(r"Q\w+\.", text)  # Check for "Q" if "IQ" not found
    if match:
        return match.group(0)[:-1]
    return None


def format_bytes(size_bytes: int) -> str:
    """
    Formats a size in bytes to a human-readable string with suffix.

    Args:
        size_bytes: Integer representing size in bytes

    Returns:
        Formatted size string with appropriate suffix
    """
    # Precomputed suffix table with single-pass conversion
    _SUFFIXES = ("B", "KB", "MB", "GB", "TB", "PB")

    if not size_bytes:
        return "0B"

    # Bitwise optimization for log2-based scaling
    magnitude = (size_bytes.bit_length() - 1) // 10

    # Clamp magnitude to prevent index out of bounds
    magnitude = min(magnitude, len(_SUFFIXES) - 1)
    scaled_size = size_bytes / (1024**magnitude)
    return f"{scaled_size:.2f} {_SUFFIXES[magnitude]}"


async def list_remote_model_tags(model_name: str, client: httpx.AsyncClient):
    response = await client.get(f"https://ollama.com/library/{model_name}/tags")
    soup = BeautifulSoup(response.text, "html.parser")

    model_entries = soup.select("div.group")
    if not model_entries:
        return []

    tags = []
    for entry in model_entries:
        # Extract model name and tag
        name_element = entry.select_one("span.group-hover\\:underline")
        if not name_element:
            continue

        full_name = name_element.text.strip()
        tag_parts = full_name.split(":")
        tag_name = tag_parts[1] if len(tag_parts) > 1 else "latest"

        size_element = entry.select_one("p.col-span-2") or entry.select_one(
            "div.text-neutral-500"
        )
        size = None
        if size_element:
            size_text = size_element.get_text(strip=True)
            size_match = re.search(r"(\d+(?:\.\d+)?[GMKT]B)", size_text)
            if size_match:
                size = size_match.group(1)

        context_element = (
            entry.select("p.col-span-2")[1]
            if len(entry.select("p.col-span-2")) > 1
            else None
        )
        context_window = None
        if context_element:
            context_window = context_element.get_text(strip=True)
        else:
            all_text = entry.get_text(separator=" ", strip=True)
            context_match = re.search(r"(\d+[KM]?) context window", all_text)
            if context_match:
                context_window = context_match.group(1)

        input_element = entry.select_one("div.col-span-2") or entry.select_one(
            "div.text-neutral-500"
        )
        input_types = []
        if input_element:
            input_text = input_element.get_text(strip=True)
            if "Text" in input_text:
                input_types.append("Text")
            if "Vision" in input_text:
                input_types.append("Vision")

        timestamp_element = entry.select_one(
            "div.flex.text-neutral-500.text-xs"
        ) or entry.select_one("div.flex.sm\\:hidden")
        updated = None
        if timestamp_element:
            timestamp_text = timestamp_element.get_text(strip=True)
            time_match = re.search(r"(\d+\s+\w+\s+ago)", timestamp_text)
            if time_match:
                updated = time_match.group(1)

        hash_element = entry.select_one("span.font-mono")
        hash_id = hash_element.get_text(strip=True) if hash_element else None

        tags.append(
            {
                "title": tag_name,
                "size": size,
                "context_window": context_window,
                "input_types": input_types,
                "updated": updated,
                "hash": hash_id,
            }
        )

    return tags


async def list_remote_models(client: httpx.AsyncClient) -> list[str] | None:
    response = await client.get(url="https://ollama.com/search")

    title_strainer = SoupStrainer("span", attrs={"x-test-search-response-title": True})
    soup = BeautifulSoup(response.text, "html.parser", parse_only=title_strainer)
    elements = soup.find_all("span", attrs={"x-test-search-response-title": True})

    if not elements:
        return None

    return [element.text.strip() for element in elements]


async def list_hugging_face_models(
    client: httpx.AsyncClient, limit: int, query: str
) -> list[dict[str, str]]:
    BASE_API_ENDPOINT = "https://huggingface.co/api/models"
    params = {
        "filter": "gguf",
        "sort": "downloads",
        "direction": "-1",
        "limit": limit,
        "full": False,
        "config": False,
        "search": query,
    }
    try:
        res = await client.get(url=BASE_API_ENDPOINT, params=params)
    except Exception:
        print(
            "❌ Failed fetching model from Hugging Face.\n>>> 🔁 Try again\n>>> 🛜 Make sure you are connected to the internet."
        )
        sys.exit(1)
    hf_response = res.json()
    payload = []

    if not hf_response:
        print(f"❌ Model not found: {query}")
        sys.exit(1)

    for response in hf_response:
        payload.append(response.get("modelId"))
    return payload


async def list_hugging_face_model_quantization(
    client: httpx.AsyncClient, model_name: str
):
    try:
        res = await client.get(
            url=f"https://huggingface.co/api/models/{model_name}?blobs=true"
        )
    except Exception:
        print(
            "❌ Failed fetching model from Hugging Face.\n>>> 🔁 Try again\n>>> 🛜 Make sure you are connected to the internet."
        )
        sys.exit(1)
    hf_response = res.json()
    payload = []
    files = hf_response.get("siblings")
    last_modified = humanized_relative_time(hf_response.get("lastModified"))
    for file in files:
        filename = file.get("rfilename")
        if filename.endswith(".gguf"):
            quantization = extract_quantization(filename)
            if not quantization:
                continue

            payload.append(
                {
                    "title": quantization,
                    "size": format_bytes(file.get("size")),
                    "updated": last_modified,
                }
            )

    return payload


@click.command(name="pull")
@click.option(
    "--hugging_face",
    "-hf",
    help="Pull models from Hugging Face",
    type=bool,
    default=False,
    is_flag=True,
)
@click.option("--query", "-q", help="Query for hugging face model", type=str)
@click.option(
    "--limit",
    "-l",
    help="Limit the number of output from hugging face. Default is 20",
    type=int,
    default=20,
)
@coro
async def pull_model(hugging_face: bool, query: str, limit: int):
    """
    Pull models from Ollama library:

    https://ollama.dev/search
    """

    console = Console()
    async with httpx.AsyncClient() as client:
        if hugging_face:
            if not query:
                query = input("🤗 hf search: ")

            with console.status("Fetching models from Hugging Face", spinner="dots"):
                models = await list_hugging_face_models(client, limit, query)
        else:
            with console.status(
                "Fetching models from Ollama directory", spinner="dots"
            ):
                models = await list_remote_models(client)

        if not models:
            print("❌ No models selected for download")
            sys.exit(0)

        model_selection = handle_interaction(
            models, title="📦 Select remote Ollama model\s:\n", multi_select=False
        )
        if model_selection:
            if hugging_face:
                with console.status("Fetching quantization levels", spinner="dots"):
                    model_tags = await list_hugging_face_model_quantization(
                        client=client, model_name=model_selection[0]
                    )
            else:
                # with console.status("Fetching model tags", spinner="dots"):
                model_tags = await list_remote_model_tags(
                    model_name=model_selection[0], client=client
                )
            if not model_tags:
                print(
                    f"❌ Failed fetching tags for: {model_selection}. Please try again."
                )
                sys.exit(1)

            title_max = size_max = context_window_max = input_type_max = updated_max = 0
            COLUMN_PADDING = 8
            for tag in model_tags:
                title_max = max(title_max, len(tag.get("title", "")))
                size_max = max(size_max, len(tag.get("size", "")))
                context_window_max = max(
                    context_window_max, len(tag.get("context_window", ""))
                )
                input_type_max = max(input_type_max, len(tag.get("input_types", "")))
                updated_max = max(updated_max, len(tag.get("updated", "")))

            if hugging_face:
                model_name_with_tags = [
                    f"{tag['title']:<{title_max + COLUMN_PADDING}}{tag['size']:<{size_max +COLUMN_PADDING}}{tag['updated']}"
                    for tag in model_tags
                ]
            else:
                model_name_with_tags = []
                for tag in model_tags:
                    display = f"{model_selection[0]}:{tag['title']:<{title_max + COLUMN_PADDING}}{tag['size']:<{size_max+COLUMN_PADDING}}"

                    if tag.get("context_window"):
                        display += f"{tag['context_window']:<{context_window_max + COLUMN_PADDING}}"

                    if tag.get("input_types"):
                        display += f"{','.join(tag['input_types']):<{input_type_max + COLUMN_PADDING}}"

                    if tag.get("updated"):
                        display += f"{tag['updated']}"

                    model_name_with_tags.append(display)
            selected_model_with_tag = handle_interaction(
                model_name_with_tags, title="🔖 Select tag/quantization:\n"
            )
            if not selected_model_with_tag:
                print("No tag selected for the model")
                sys.exit(1)

            if hugging_face:
                final_model = (
                    f"hf.co/{model_selection[0]}:{model_name_with_tags[0]}".split()[0]
                )
            else:
                final_model = selected_model_with_tag[0].split()[0]
            print(f">>> Pulling model: {final_model}")
            try:
                response = ollama.pull(final_model, stream=True)
                screen_padding = 100

                for data in response:
                    out = f"Status: {data.get('status')} | Completed: {format_bytes(data.get('completed'))}/{format_bytes(data.get('total'))}"
                    print(f"{out:<{screen_padding}}", end="\r", flush=True)

                print(f"\r{' ' * screen_padding}\r")  # Clear screen
                print(f"✅ {final_model} model is ready for use!\n\n>>> olm run\n")
            except Exception as e:
                print(f"❌ Failed downloading {final_model}\n{str(e)}")
