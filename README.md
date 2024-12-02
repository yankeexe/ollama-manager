# 🦙 Ollama Manager [WIP]

![Python Version](https://img.shields.io/badge/Python-3.11-brightgreen?style=flat-square)

CLI app to manage Ollama models.

<a href="https://youtu.be/1y2TohQdNbo">
<img src="https://i.imgur.com/iA0LB0e.gif" width="800">
</a>

## ⚡️ Features

- List and Download Remote models from [Ollama library](https://ollama.dev/models)
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

### Delete Local Model/s

Delete a single model

```sh
olm rm
```

Delete multiple models

```sh
olm rm -m
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

⚠️ Only text-based models are supported right now.

You need to install optional dependencies for this:

```sh
pip install ollama-manager[ui]
```

then use the following command to select the model:

```sh
olm run -ui
```

## Getting Help

```sh
olm --help

olm <sub-command> --help
```
