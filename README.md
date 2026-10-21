# 🗂️ Flashcard App

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](#-license)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![codecov](https://codecov.io/github/ScotRossman/flashCards/graph/badge.svg?token=GEPWWJL3B5)](https://codecov.io/github/ScotRossman/flashCards)
A Python flashcard application for studying and retaining information, starting with a terminal interface and designed to grow into a GUI and web app.

---

## 📑 Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [Development](#-development)
- [Continuous Integration](#-continuous-integration)
- [Roadmap](#-roadmap)
- [License](#-license)

---

## 🚀 Features

- **Interactive terminal study sessions:** create, review, and manage flashcards from the command line.
- **Installable command:** installs a `flashcards` command via the project's console-script entry point.
- **Editable installs:** code changes take effect on the next run without reinstalling.
- **Automated quality checks:** formatting with `black`, tests with `pytest` and `pytest-cov`.
- **CI pipeline:** GitHub Actions validates every push and pull request to `dev`, with coverage reported to Codecov.

---

## ⚡ Quick Start

**Requirements:** Python 3.10 or newer and `git`.

```bash
# 1. Clone the repository
git clone https://github.com/ScotRossman/flashCards.git
cd flashCards

# 2. Create and activate a virtual environment
python -m venv .venv

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

# 3. Install the app with development tools (editable mode)
python -m pip install --upgrade pip
pip install -e ".[dev]"
pip install pytest-cov

# 4. Run it
flashcards
```

> **Tip:** if the `flashcards` command isn't found, make sure your virtual environment is activated, or run the module directly with `python -m flashcardApp.main`.

---

## 💻 Usage

Launch the app from anywhere inside your activated environment:

```bash
flashcards
```

Because the project is installed in editable mode (`pip install -e`), edit the code in your IDE and simply re-run the command to see your changes.

---

## 🧱 Project Structure

```text
flashCards/
├── src/
│   └── flashcardApp/
│       ├── main.py          # Entry point (start() is wired to the `flashcards` command)
│       ├── operations.py    # Flashcard and study logic
│       └── constants.py     # Shared constants
├── tests/                   # pytest test suite
├── pyproject.toml           # Packaging, dependencies, tool configuration
└── README.md
```

---

## 🛠️ Development

### Dependencies

| Group   | Install command            | Contents                              |
| ------- | -------------------------- | ------------------------------------- |
| Core    | `pip install -e .`         | `click`, `pydantic`                   |
| Dev     | `pip install -e ".[dev]"`  | `pytest`, `black`, `flake8`           |
| GUI     | `pip install -e ".[gui]"`  | `PyQt6` *(planned)*                   |
| Web     | `pip install -e ".[web]"`  | `fastapi`, `uvicorn` *(planned)*      |

### Run the tests

```bash
pytest --cov=./src --cov-report=xml
```

**Tests hang?** Interactive menu prompts can wait for input while `pytest` captures output. Disable capturing and enable verbose mode to see where it's waiting:

```bash
pytest --cov=./src --cov-report=xml -v -s
```

### Check and apply formatting

```bash
black --check src/ tests/   # verify only
black src/ tests/           # auto-format
```

### Lint

```bash
flake8 src/ tests/
```

---

## 🤖 Continuous Integration

GitHub Actions runs on every push and pull request to the `dev` branch:

1. **Formatting:** `black --check` enforces a consistent style.
2. **Testing:** the full `pytest` suite runs.
3. **Coverage:** reports upload to [Codecov](https://codecov.io) so you can track code health over time.

---

## 🗺️ Roadmap

- [x] Command-line interface
- [ ] Desktop GUI (`gui` extra)
- [ ] Web interface (`web` extra)
- [ ] Raise test coverage across `main.py` and `operations.py`

---

## 📄 License

Released under the [MIT License](https://opensource.org/licenses/MIT).

---

*Built by Scot Rossman as a hands-on Python learning project.*
