# Flashcard App 🗂️

[![codecov](https://codecov.io)](https://codecov.io)

An interactive, Python-based flashcard application built to help users study and retain information. The project is designed with live-development workflows, automated formatting checks, and a continuous integration pipeline.

## 🚀 Features
* **Interactive Flashcards:** Create, review, and manage study decks dynamically via the terminal.
* **Live Development Mode:** Mounted in editable mode so changes update instantly during debugging.
* **Format Compliance:** Automatically checked using `black` to ensure clean code architecture.
* **Comprehensive Test Suite:** Powered by `pytest` and `pytest-cov` to track execution safety.

---

## 🛠️ Local Development Setup

Follow these steps to set up the project on your local machine.

### 1. Clone the Repository
```bash
git clone https://github.com
cd flashCards
```

### 2. Set Up a Virtual Environment (Recommended)
```bash
python -m venv .venv
# Activate on Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Activate on macOS/Linux:
source .venv/bin/activate
```

### 3. Install Dependencies & Live-Mount
Install development utilities and mount the application in **editable mode**. This links Python directly to your source files so that **any changes you make apply instantly** without restarting or reinstalling:
```bash
pip install --upgrade pip
pip install build black pytest pytest-cov
pip install -e .
```

---

## 💻 Running & Debugging the App

### Run the App Locally
Because the app is installed in editable mode, you can launch it anytime by running:
```bash
python src/main.py
```
*Feel free to make code changes in your IDE; the live app will reflect those updates immediately on the next execution.*

---

## 🧪 Testing & Code Quality

### Run the Test Suite
To run all tests and generate a code coverage report locally:
```bash
pytest --cov=./src --cov-report=xml
```

### Debugging Hanging Tests
If your interactive menu prompts cause `pytest` to hang or freeze locally, disable output capturing and turn on verbose mode to see exactly where the loop is waiting:
```bash
pytest --cov=./src --cov-report=xml -v -s
```

### Check Code Formatting
Verify that your code complies with the project's style guide before pushing:
```bash
black --check src/ tests/
```

---

## 🤖 Continuous Integration (CI)

This repository utilizes **GitHub Actions** to automatically validate code quality on every push or pull request to the `dev` branch. The workflow ensures:
1. **Formatting:** Validates code style consistency using `black`.
2. **Testing:** Executes the full `pytest` suite matrix.
3. **Codecov Integration:** Automatically uploads reports and tracks code health metrics. You can view the live interactive coverage dashboards directly on [Codecov](https://codecov.io).
