# API Test Issues Encountered

This document outlines the primary difficulties encountered while attempting to get the `pytest` test suite to pass, specifically concerning API-related tests.

## 1. Missing `API_SECRET_KEY` Environment Variable
- **Issue:** Many API tests (e.g., `tests/accounting/test_api.py`, `tests/api/test_auth_api.py`) fail during collection because `api/auth.py` raises a `RuntimeError` if the `API_SECRET_KEY` environment variable is not set.
- **Attempted Fix:** Running `pytest` with `API_SECRET_KEY=testsecret pytest tests/` resolved the immediate `RuntimeError` but revealed further issues.
- **Status:** Workaround available for local testing, but a proper configuration management for test environments is needed.

## 2. Missing `python-multipart` Dependency
- **Issue:** After resolving the `API_SECRET_KEY` issue, API tests started failing with `RuntimeError: Form data requires "python-multipart" to be installed`. This is a FastAPI dependency for handling `OAuth2PasswordRequestForm` and other form data.
- **Attempted Fix:** Added `python-multipart>=0.0.5` to `requirements.txt` and installed it.
- **Status:** This specific error seems resolved after installation.

## 3. Persistent `SyntaxError` in `api/products.py`
- **Issue:** A `SyntaxError: parameter without a default follows parameter with a default` is consistently reported at line 96 of `api/products.py`, specifically pointing to the `request: Request` parameter in the `get_all_products_api` function signature.
- **Attempts:**
    - Verified the parameter order, which seemed correct according to Python rules (non-default `request` before defaulted `Query` and `Depends` parameters).
    - Changed `request: Request` to `request: Request = Depends()` to give it an explicit default from FastAPI's perspective. The error persisted.
    - Simplified the function signature to `async def get_all_products_api(request: Request)` (commenting out other parameters). The error still pointed to this line.
    - Moved `request: Request` to be the last parameter. The error still persisted, highlighting the `request: Request` part.
- **Status:** This is a major blocker for collecting most API tests, as `api/main.py` imports `api/products.py`. The exact cause is unclear but might be related to `pytest`'s AST interaction with FastAPI/Pydantic type hints or a very subtle syntax issue not apparent in `read_files` output.

## 4. `ImportError: cannot import name 'get_db' from 'api.dependencies'`
- **Issue:** Several API route modules (e.g., `api/employee_documents.py`, `api/employees.py`) attempt to import `get_db` from `api/dependencies.py`, but it's not defined there.
- **Attempted Fix:**
    - Identified that `api/dependencies.py` was missing this function.
    - Added a `get_db` async generator function to `api/dependencies.py`. This function uses a mock `SessionLocal` for now, as the actual SQLAlchemy `SessionLocal` setup for the main application (outside of the `accounting` module's test setup) is not clearly defined in `db/connection.py` or a `db/database.py`.
- **Status:** The import error itself should be resolved by the addition of `get_db`. However, any test that relies on this `get_db` for actual database operations will likely fail or not behave as expected until a proper `SessionLocal` is provided and used by `get_db`.

## 5. Other `ModuleNotFoundError` and `ImportError` Issues
- Several other module-level import errors were noted for packages like `icalendar`, `reportlab`, `PyQt5.QtWebEngineWidgets`, and for internal project paths (e.g., `db.database_manager`, `utils.text_extraction`).
- **Attempts:** Added `icalendar`, `reportlab`, `PyQtWebEngine` to `requirements.txt` and installed.
- **Status:** Some of these might be resolved by the installations. Others, especially internal project path issues (like `db.database_manager` which doesn't seem to exist) or misnamed imports (`add_user_direct` instead of `add_user_crud`), still need to be addressed systematically. The `PyQtWebEngineWidgets` error might also indicate a deeper Qt environment issue with `pytest-qt`.

## Recommendation
Focus on stabilizing the core application and non-API tests first. A dedicated effort will be needed to set up a robust testing environment for the FastAPI parts, including:
- Proper SQLAlchemy session management for tests.
- Consistent handling of environment variables like `API_SECRET_KEY`.
- Resolving the `SyntaxError` in `api/products.py`.
- Systematically fixing all other import and syntax errors in the API test files.
