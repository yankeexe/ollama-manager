# 🦙 Ollama Manager

![Python Version](https://img.shields.io/badge/Python-3.11-brightgreen?style=flat-square)
![Downloads](https://static.pepy.tech/badge/ollama-manager)


CLI app to manage Ollama models.

<a href="https://youtu.be/1y2TohQdNbo">
<img src="https://i.imgur.com/iA0LB0e.gif" width="800">
</a>

## ⚡️ Features

- List and Download Remote models from [🦙 Ollama library](https://ollama.dev/models) or [🤗 Hugging Face](https://huggingface.co/models?sort=trending&search=gguf)
- Delete existing Ollama models
- Launch models in Streamlit UI
- Fuzzy Search


## 🚀 Installation

```sh
pip install ollama-manager

# OR

pipx install ollama-manager
```

For development: installs app in editable mode

```sh
make setup
```

## ✨ Usage

### Pull Remote Model

```sh
olm pull
```

Pull Hugging Face models:

```sh
olm pull -hf

# With query:

olm pull -hf -q llama3.2

# With limit:

olm pull -hf -q llama3.2 -l 10

# With multimodal capabilities:

olm pull -hf -q llama -mm
```

### Delete Local Model/s

Delete a single model

```sh
olm rm
```

Delete multiple models

```sh
olm rm -m
```

Delete model without confirmation prompt:

```sh
olm rm -y
```

### Run selected model

Run the selected model on Ollama terminal UI:

```sh
olm run
```

---

**Run models in a Streamlit UI:**

<details>
<summary>Ollama Manager UI</summary>
<img src="https://i.imgur.com/UqQLjXx.gif" width="800" />
</details>

You need to install optional dependencies for this:

```sh
pip install ollama-manager[ui]
```

then use the following command to select the model:

```sh
# For Text Models
olm run -ui text

# For Vision Models

olm run -ui vision
```

### List models

List your downloaded ollama models with a rich formatted table:

```sh
olm list
```

Sort models by `name`, `date` or `size` (default is `name`):

```sh
olm list --sort name  # Sort alphabetically by model name
olm list -s date      # Sort by modification date
olm list -s size      # Sort by model size
```

Control the sort order with `--order` or `-o` (default is `asc`):

```sh
olm list --sort size --order desc  # Largest models first
olm list -s date -o desc           # Most recently modified first
olm list -s name -o asc            # Alphabetical A-Z
```


## Getting Help

```sh
olm --help

olm <sub-command> --help
```
