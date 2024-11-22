# 🦙 Ollama Manager [WIP]

![Python Version](https://img.shields.io/badge/Python-3.11-brightgreen?style=flat-square)

CLI app to manage Ollama models.

<a href="https://youtu.be/1y2TohQdNbo">
<img src="https://i.imgur.com/iA0LB0e.gif" width="800">
</a>

## ⚡️ Features

- List and Download Remote models from [Ollama library](https://ollama.dev/models)
- Delete existing Ollama models
- Fuzzy Search


## 🚀 Installation

```sh
make setup
```

Install the app in editable mode:

```sh
pip install -e .
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

## Getting Help

```sh
olm --help

olm <sub-command> --help
```
