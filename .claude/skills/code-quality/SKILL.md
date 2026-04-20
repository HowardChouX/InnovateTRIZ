---
name: code-quality
description: Use when asked to run linting, formatting, or type checking on the InnovateTRIZ codebase.
---

## Code Formatting

Format all Python code with Black:

```bash
cd /home/chou/triz-app && black src/ tests/
```

## Linting

Run Ruff linter:

```bash
cd /home/chou/triz-app && ruff check src/ tests/
```

Auto-fix fixable issues:

```bash
cd /home/chou/triz-app && ruff check --fix src/ tests/
```

## Type Checking

Run MyPy type checker:

```bash
cd /home/chou/triz-app && mypy src/
```

## Combined Quality Check

Run all checks in sequence:

```bash
cd /home/chou/triz-app && black --check src/ tests/ && ruff check src/ tests/ && mypy src/
```

## Quality Standards

- Follow PEP 8 style
- Use type hints where possible
- Keep lines under 88 characters
- No unused imports
- Public API functions should have docstrings
- Async functions use `async def` with `await page.update_async()`

## Common Issues

| Issue | Solution |
|-------|---------|
| MyPy errors | Verify type hints are correct, add `# type: ignore` if needed |
| Ruff errors | Use `--fix` to auto-fix, or adjust manually |
| Black formatting conflicts | Ensure latest version: `black --version` |
