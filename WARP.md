# WARP.md - AI Agent Instructions

This document provides context and guidelines for AI assistants working with this FastAPI project.

## 🎯 Project Overview

**Name:** ai-app-scaffolding  
**Type:** FastAPI REST API template with AI capabilities  
**Language:** Python 3.9+  
**Framework:** FastAPI  
**Package Manager:** Poetry  
**Testing:** pytest

## 🏗️ Architecture

This is a layered FastAPI application following clean architecture principles:

- **API Layer** (`src/api/v1/`): REST endpoints, request/response handling
- **Services Layer** (`src/services/`): Business logic
- **Models Layer** (`src/models/`): Pydantic schemas for validation
- **Core Layer** (`src/core/`): Configuration, settings, base utilities
- **Helpers** (`src/helpers/`): Application-specific helper functions
- **Utils** (`src/utils/`): Generic reusable utilities
- **Exceptions** (`src/exceptions/`): Custom error handling

## 🔧 Development Commands

### Installation & Setup
```bash
poetry install                    # Install all dependencies
poetry env info --path            # Get virtual environment path
```

### Running the Application
```bash
poetry run start                  # Start the FastAPI server (default: http://127.0.0.1:8001)
```

### Testing
```bash
poetry run test                   # Run all tests
poetry run test -v                # Verbose output
poetry run test tests/unit/       # Unit tests only
poetry run test tests/integration/ # Integration tests only
poetry run test -k "keyword"      # Run specific tests by keyword
```

### Code Quality
```bash
poetry run pre-commit run --all-files  # Run all pre-commit hooks
poetry run pre-commit install          # Install pre-commit hooks
poetry run black .                     # Format code
poetry run isort .                     # Sort imports
poetry run flake8                      # Lint code
poetry run mypy src/                   # Type checking
```

### Dependency Management
```bash
poetry add <package>              # Add runtime dependency
poetry add --group dev <package>  # Add dev dependency
poetry update                     # Update dependencies
poetry show                       # List installed packages
```

## 📝 Coding Standards

### Style Guidelines
- **Formatter:** Black (line length: 88)
- **Import Sorting:** isort (profile: black)
- **Linter:** Flake8
- **Type Checker:** mypy with Pydantic plugin

### Project Conventions
1. **Imports:** Use absolute imports from `src` (e.g., `from src.core.config import settings`)
2. **Type Hints:** All functions must have type annotations
3. **Pydantic Models:** Use for all request/response schemas
4. **Async/Await:** Prefer async endpoints for I/O operations
5. **Error Handling:** Use custom exceptions from `src/exceptions/`

### File Naming
- **Python files:** `snake_case.py`
- **Classes:** `PascalCase`
- **Functions/Variables:** `snake_case`
- **Constants:** `UPPER_SNAKE_CASE`

## 🔍 Key Files

| File | Purpose |
|------|---------|
| `src/main.py` | FastAPI app instantiation and configuration |
| `src/run.py` | Application entry point using uvicorn |
| `src/core/config.py` | Configuration management with Pydantic Settings |
| `src/api/v1/api_router.py` | API version 1 router aggregation |
| `src/api/v1/dependencies.py` | Shared FastAPI dependencies |
| `pyproject.toml` | Project metadata and dependencies |
| `.env` | Environment variables (not in version control) |
| `.env.example` | Example environment configuration |

## 🧪 Testing Guidelines

### Test Structure
```
tests/
├── unit/           # Unit tests (mock all external dependencies)
└── integration/    # Integration tests (test component interactions)
```

### Testing Principles
- **Mock external APIs:** Always mock service layer dependencies
- **Use fixtures:** Create reusable pytest fixtures
- **Async tests:** Use `pytest-asyncio` for async endpoint testing
- **Coverage:** Aim for comprehensive test coverage
- **Isolation:** Tests should be independent and idempotent

### Example Test Structure
```python
import pytest
from httpx import AsyncClient
from src.main import app

@pytest.mark.asyncio
async def test_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/endpoint")
        assert response.status_code == 200
```

## 🌐 Environment Configuration

Required environment variables (see `.env.example`):
- `APP_HOST`: Server host (default: "localhost")
- `APP_PORT`: Server port (default: "8001")
- `DEBUG_MODE`: Enable debug mode (default: false)
- `LOG_LEVEL`: Logging level (default: "info")

**Security Note:** Never commit `.env` to version control. It's in `.gitignore`.

## 📚 API Documentation

FastAPI generates automatic interactive documentation:
- **Swagger UI:** http://127.0.0.1:8001/docs
- **ReDoc:** http://127.0.0.1:8001/redoc

## 🚨 Common Issues & Solutions

### VSCode Import Detection
If imports aren't detected:
1. Run `poetry env info --path`
2. Create `.vscode/settings.json` with the virtual environment path
3. Set Python interpreter in VSCode (Ctrl+Shift+P → "Python: Select Interpreter")

### Windows: No pyvenv.cfg file
```powershell
poetry env remove python
poetry install
```

### Pre-commit Hook Failures
```bash
poetry run pre-commit run --all-files  # See what's failing
poetry run black .                     # Auto-fix formatting
poetry run isort .                     # Auto-fix imports
```

## 🤖 AI Agent Guidelines

When working with this codebase:

1. **Always run tests** after making changes: `poetry run test`
2. **Check code quality** before suggesting code: `poetry run pre-commit run --all-files`
3. **Follow the architecture**: Don't mix layers (e.g., business logic in routers)
4. **Use type hints**: All new code should be fully typed
5. **Update tests**: Add/update tests for any code changes
6. **Respect conventions**: Match existing patterns in the codebase
7. **Environment safety**: Never commit secrets or `.env` files
8. **Mock external calls**: Don't make real API calls in tests

### Adding New Endpoints
1. Create router in `src/api/v1/routers/`
2. Add Pydantic models in `src/models/`
3. Implement business logic in `src/services/`
4. Register router in `src/api/v1/api_router.py`
5. Add tests in `tests/`
6. Run `poetry run test` to verify

### Modifying Existing Code
1. Read the file to understand current implementation
2. Make targeted changes following existing patterns
3. Update related tests
4. Run `poetry run test` and `poetry run pre-commit run --all-files`
5. Verify API documentation at `/docs`

## 📦 Dependencies

### Runtime Dependencies
- **fastapi**: Web framework with OpenAPI support
- **pydantic**: Data validation and settings management
- **uvicorn**: ASGI server
- **colorlog**: Colored logging output

### Development Dependencies
- **pytest**: Testing framework
- **pytest-asyncio**: Async test support
- **pytest-mock**: Mocking utilities
- **httpx**: HTTP client for testing
- **black**: Code formatter
- **isort**: Import sorter
- **flake8**: Linter
- **mypy**: Type checker
- **pre-commit**: Git hook framework

## 🔗 Project Resources

- **API Docs (Swagger):** http://127.0.0.1:8001/docs
- **API Docs (ReDoc):** http://127.0.0.1:8001/redoc
- **FastAPI Documentation:** https://fastapi.tiangolo.com/
- **Poetry Documentation:** https://python-poetry.org/docs/
- **Pydantic Documentation:** https://docs.pydantic.dev/

---

**Last Updated:** 2025-11-03  
**Template Version:** 0.1.0
