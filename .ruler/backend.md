# AI Agent Instructions for backend/

All the following instructions must be followed when writing code in the ./backend/ directory.
This includes all Python code, tests, and any other files related to the backend project.

## Coding Standards

- Use Python 3.14 and Django 5.2 conventions.
- Always follow PEP8 and Python best practices for style and structure with a line length of 120.
- Name variables, functions, and classes descriptively and consistently.
- Write modular code: split logic into reusable functions and classes.
- Add concise docstrings to all public functions and classes.
- Don't use hardcoded strings, if possible.
  If a function exists to generate that string, use it.
  If the string is a constant, define it in its (or another appropriate) module.
- Never use `__future__` imports.
- Use type hints for all arguments and return values.
- Use type annotations for all variables, and functions.
- When having to run code, use uv to run the project and always use the `--active` flag: `uv run --active`.
- The code is formatted using `ruff` exclusively. The most used command to run is:
  `ruff format . && ruff check --select I --fix ./ && ruff check --fix ./`

## Template Standards

- Use Django's template language for all HTML templates.
- Use Tailwind CSS 4 for styling, and ensure it is properly integrated with Django templates.
- Use Alpine.js 3 for any necessary JavaScript interactivity in templates.
- Follow best practices for template structure and organization.
- Use template inheritance to avoid duplication.
- Name templates descriptively and consistently.
- Avoid logic in templates; keep it in views or template tags.

## Testing Requirements

- Store tests in `tests.py` or a `tests/` directory within each app.
- Use Django's `TestCase` for all unit and integration tests.
- Write tests for every new feature, model, and view.
- Ensure tests are independent and do not rely on external state.
- Name test methods clearly and assert expected results.

## Dependency Management

- Add dependencies using uv: `uv pip install <package>`.
- Let uv update `pyproject.toml` and `uv.lock` automatically.
- Never manually edit `uv.lock`.

## Django Project Practices

- Register new models in `admin.py` for admin access.
- Create and apply migrations for model changes.
- Keep Django settings modular and environment-specific in `settings/`.

## Commit and Workflow

- Ensure code is formatted and linted before commit.
- Include tests for new features and bug fixes.
- Write clear commit messages describing changes.

## Summary

Follow these instructions to ensure code quality, maintainability, and reliability in the backend project.
All code, tests, formatting, and dependencies must comply with these rules.
