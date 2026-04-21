---
name: run-triz-tests
description: Use when asked to run tests for the InnovateTRIZ app.
---

## Run All Tests

```bash
cd /home/chou/triz-app && pytest tests/ -v
```

## Run Specific Test File

```bash
cd /home/chou/triz-app && pytest tests/test_core.py -v
```

## Run with Coverage

```bash
cd /home/chou/triz-app && pytest tests/ -v --cov=src --cov-report=term-missing
```

## Filter by Keyword

```bash
cd /home/chou/triz-app && pytest tests/ -v -k "matrix"
```

## Desktop Mode Verification

For UI-related tests, verify in desktop mode first:

```bash
cd /home/chou/triz-app && python main.py --mode desktop
```

## Continuous Integration

All tests must pass before merging. See `tests/` directory for the test suite.

## Test Structure

```
tests/
├── conftest.py          # pytest fixtures
├── test_core.py         # Core logic (TRIZ Engine, Matrix Selector)
├── test_triz_constants.py # Data loader
├── test_ai_client.py    # AI client
└── test_ui/            # UI component tests
```

## Common Issues

| Issue | Solution |
|-------|---------|
| Import errors | Run from project root or set `PYTHONPATH` |
| Async test failures | Use `@pytest.mark.asyncio` decorator |
| Coverage is 0 | Verify module path is correct |
