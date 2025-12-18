# ai-app-scaffolding
Template for future FastAPI projects with AI

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](...) [![License](https://img.shields.io/badge/License-MIT-blue)](LICENSE) [![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](...)

## 🗂️ Project Structure

```
ai-app-scaffolding
├── assets/                     # Container for assets
├── src/                        # Main application code
│   ├── api/                    # API Layer: Routers & Endpoints
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── dependencies.py # Centralize and organize shared dependency functions.
│   │       ├── api_router.py   # Aggregates v1 routers
│   │       └── routers/        # Endpoint definitions (input.py)
│   │           ├── __init__.py
│   │           └── input.py
│   ├── core/                   # Core logic, config, settings
│   ├── exceptions/             # Custom application exceptions
│   ├── helpers/                # Contains application-specific helper functions that assist higher-level business logic, services, or API endpoints.
│   ├── models/                 # Pydantic models
│   ├── services/               # Business logic services
│   ├── utils/                  # Contains generic, reusable utility functions and modules that are independent of application-specific logic.
│   └── main.py                 # FastAPI app instantiation
│   └── run.py                  # Runs main.py using uvicorn
├── tests/                      # Tests (unit, integration)
├── exports/                    # Container for generated files
├── .env.example                # Example environment variables
├── .flake8                     # Flake8 config file
├── .gitignore                  # Specifies which files and directories Git should ignore
├── .pre-commit-config.yaml     # Configuration file for pre-commit hooks
├── mypi.ini                    # Mypy config file
├── poetry.lock                 # Lock file containing exact versions of dependencies
├── pyproject.toml              # Project configuration and dependencies managed by Poetry
└── README.md
```

## Prerequisites
Before you begin, ensure you have the following installed:

* **Python:** 3.9 or higher (Recommended, check your project's exact requirement)
* **Git:** Version control system
* **poetry:** tool for dependency management and project packaging
---
## 🛠️ Installing Poetry
 📦 **Linux (Ubuntu/WSL)**

1. Install `pipx` and `poetry` using the following commands:
    ```bash
    sudo apt update
    sudo apt install pipx
    pipx install poetry
    pipx ensurepath
    ```
2. Reboot your WSL session or Linux OS to apply changes.

---

 📦 **macOS (Untested)**

1. Install `poetry` using the following commands:
    ```bash
    curl -sSL https://install.python-poetry.org | python3 -
    ```
2. Restart your terminal or reboot your system to apply changes.

---

 🪟 **Windows**

1. Install **Python 3.9 or above** from the [Python Official](https://www.python.org/downloads/windows/) and make sure to check "**Add Python to PATH**".
2. Open **PowerShell**.
3. Run the following command to install Poetry:
    ```powershell
    (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
    ```
4. In the same terminal, follow **Option A** from the Poetry installer output and copy the code inside the triple backticks (` ``` `).
5. Restart the terminal to finalize the setup.

## Configuration
The application uses environment variables for configuration, loaded via Pydantic Settings (app/core/config.py).

1.  **Create `.env` File:** In the project root directory `(ai-app-scaffolding/)`, create a file named `.env.` You can copy `.env.example` if one exists.
2.  **Add API Keys and Settings:** Edit the `.env` file and add your API keys obtained from the respective providers.
    ```bash
    # .env Example Content
    APP_HOST=127.0.0.1
    APP_PORT=8001
    # --- Optional Settings ---
    # LOG_LEVEL="INFO" # Example: Set logging level (DEBUG, INFO, WARNING, ERROR)
    # DEBUG_MODE=True
    ```
3.  **Security:** Crucially, ensure `.env` is listed in your `.gitignore file` to prevent accidentally committing sensitive keys to version control. Use environment variables directly or other secrets management tools in production environments.


## API Documentation
FastAPI automatically generates interactive API documentation. Once the server is running, access it via your browser:
* **Swagger UI:** `http://127.0.0.1:8001/docs` (or your configured address)
* **ReDoc:** `http://127.0.0.1:8001/redoc` (or your configured address)


## Running the Application (Local Development)
1.  Verify your `.env` file is correctly populated.
2.  Install dependencies
    ```bash
    poetry install
    ```
3. Run the application using
    ```bash
    poetry run start
    ```
4.  The API will typically be available at `http://127.0.0.1:8001` (or the host/port you configured). Check the startup logs for the exact address.


## Testing
The project uses `pytest`. Tests should primarily mock service layer dependencies or adapter calls to avoid external API usage.

1.  **Install Test Dependencies:**
    ```bash
    poetry install
    ```
2.  **Run Tests:** (From project root)
    ```bash
        poetry run test # Run all tests
        poetry run test -v # Verbose output
        poetry run test tests/unit/ # Run unit tests only
        poetry run test tests/integration/ # Run integration tests only
        poetry run test -k "test_post_input_missing_body" # Run tests matching keyword
    ```

## Managing Dependencies with Poetry

Use the following commands to add dependencies to the project using [Poetry](https://python-poetry.org/).

### Add a Runtime Dependency
To add a package needed at runtime:
```bash
poetry add <package-name>
```

### Add a Development Dependency
To add a package used only during development (e.g. testing, linting):
```bash
poetry add --group dev <package-name>
```


## 🧹 Pre-commit Hooks

This project uses [pre-commit](https://pre-commit.com/) to automatically check code quality before you commit.

### Install pre-commit hooks:
```bash
poetry run pre-commit install
```

### Run all hooks manually:

```bash
poetry run pre-commit run --all-files
```

### Update hooks:

```bash
poetry run pre-commit autoupdate
```
---
# ⚠️ Known Issues
## Imports missing in VSCode
>If VSCode can't detect your imports after running `poetry install`, follow these steps:

### 1. Get the Poetry virtual environment path

Open a terminal at the root of your project and run:

```bash
poetry env info --path
```
### 2. You’ll get something like:
```powershell
/home/youruser/.cache/pypoetry/virtualenvs/src-abc123-py3.11
```
### 3. Create file `.vscode/settings.json`
```json
{
  // 👇 Set Python interpreter path from `poetry env info --path`
  "python.defaultInterpreterPath": "<copy_path_from_step_2>",

  // 🛑 Optional: Hide Git-related and ignored files in Explorer
  "files.exclude": {
    "**/.git": true,
    "**/.DS_Store": true
  },
  "explorer.excludeGitIgnore": true
}
```
>⚠️ On Windows, replace /bin/python with \\Scripts\\python.exe
### 4  Open the command palette in VSCode
* Press Ctrl+Shift+P (or Cmd+Shift+P on Mac)
* Type and select: Python: Select Interpreter
* Click the ⚙️ gear icon next to "Enter interpreter path"
* Choose “Use Python from `python.defaultInterpreterPath` setting”

##  🪟 **Windows** No pyvenv.cfg file
>If errors like ``No pyvenv.cfg file`` occurs when using ``poetry <commands>``
### Recreate the environment
```powershell
    poetry env remove python
    poetry install
```
This will:
* Delete the broken virtual environment
* Create a new one
* Reinstall dependencies from pyproject.toml