import datetime
import re
import sys

import click
import httpx
import ollama
from bs4 import BeautifulSoup, SoupStrainer

from ollama_manager.utils import coro, handle_interaction


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


def humanized_relative_time(datetime_str: str):
    """
    Converts a datetime string in ISO 8601 format to a human-readable relative time.

    Args:
        datetime_str: The datetime string in "YYYY-MM-DDTHH:MM:SS.mmmZ" format.

    Returns:
        A human-readable string representing the relative time, or the original
        datetime string if it cannot be parsed.
    """
    try:
        dt = datetime.datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
    except ValueError:
        return datetime_str  # Return original if parsing fails

    now = datetime.datetime.now(tz=datetime.timezone.utc)
    delta = now - dt

    if delta < datetime.timedelta(minutes=1):
        return "just now"
    elif delta < datetime.timedelta(hours=1):
        minutes = int(delta.total_seconds() // 60)
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    elif delta < datetime.timedelta(days=1):
        hours = int(delta.total_seconds() // 3600)
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif delta < datetime.timedelta(days=30):
        days = delta.days
        return f"{days} day{'s' if days > 1 else ''} ago"
    elif delta < datetime.timedelta(days=365):
        months = int(delta.days // 30)
        return f"{months} month{'s' if months > 1 else ''} ago"
    else:
        years = int(delta.days // 365)
        return f"{years} year{'s' if years > 1 else ''} ago"


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
    res = await client.get(url=BASE_API_ENDPOINT, params=params)
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
    res = await client.get(
        url=f"https://huggingface.co/api/models/{model_name}?blobs=true"
    )
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
    from rich.console import Console

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
                with console.status("Fetching model tags", spinner="dots"):
                    model_tags = await list_remote_model_tags(
                        model_name=model_selection[0], client=client
                    )
            if not model_tags:
                print(
                    f"❌ Failed fetching tags for: {model_selection}. Please try again."
                )
                sys.exit(1)

            max_length = max(
                len(f"{model_selection}:{tag['title']}") for tag in model_tags
            )

            if hugging_face:
                model_name_with_tags = [
                    f"{tag['title']:<{max_length}}{tag['size']:<{max_length}}{tag['updated']}"
                    for tag in model_tags
                ]
            else:
                model_name_with_tags = [
                    f"{model_selection[0]}:{tag['title']:<{max_length + 5}}{tag['size']:<{max_length + 5}}{tag['updated']}"
                    for tag in model_tags
                ]
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

                print(f'\r{" " * screen_padding}\r')  # Clear screen
                print(f"✅ {final_model} model is ready for use!\n\n>>> olm run\n")
            except Exception as e:
                print(f"❌ Failed downloading {final_model}\n{str(e)}")
