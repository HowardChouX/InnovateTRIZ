---
name: create-triz-tests
description: Use when asked to create or update tests for the InnovateTRIZ Flet application, including unit tests and integration tests.
---

## When to Use

- Unit tests for core logic (TRIZ engine, matrix selector, AI client)
- Integration tests for UI components (MatrixTab, PrinciplesTab, SettingsTab)
- Regression tests for bug fixes
- Data integrity validation tests

## Test Structure

```
tests/
├── conftest.py          # pytest fixtures
├── test_core.py         # Core logic tests (TRIZ Engine, Matrix Selector)
├── test_triz_constants.py # Data loader tests
├── test_ai_client.py    # AI client tests
└── test_ui/            # UI component tests
    └── ...
```

## Fixture Usage

Prefer fixtures defined in `tests/conftest.py`.

## Authoring Workflow

1. Identify behavior to verify
2. Build deterministic test data/state
3. Use `@pytest.mark.asyncio` for async tests
4. Name clearly: `test_<feature>_<behavior>`
5. Run target test file
6. Verify all tests pass

## Assertion Patterns

### Functional assertion

```python
def test_matrix_selector_returns_valid_principles():
    from src.core.matrix_selector import get_matrix_manager
    manager = get_matrix_manager()
    result = manager.get_principles("improve_36", "worsen_33")
    assert len(result) > 0
```

### Async test

```python
import pytest

@pytest.mark.asyncio
async def test_ai_client_connectivity():
    from src.ai.ai_client import get_ai_manager
    manager = get_ai_manager()
    result = await manager.check_connectivity()
    assert isinstance(result, bool)
```

### Data integrity test

```python
def test_triz_data_loader_completeness():
    from src.data.triz_constants import get_triz_data_loader
    loader = get_triz_data_loader()
    assert len(loader.get_all_params()) == 39
    assert len(loader.get_contradiction_matrix()) > 0
    assert len(loader.get_40_principles()) == 40
```

## Run Commands

```bash
cd /home/chou/triz-app

# Run all tests
pytest tests/ -v

# Run single test file
pytest tests/test_core.py -v

# With coverage
pytest tests/ -v --cov=src --cov-report=term-missing

# Filter by keyword
pytest tests/ -v -k "matrix"
```

## Quality Checklist

- [ ] Test file location matches source area
- [ ] Tests are deterministic (no random/time-varying content)
- [ ] Tests clean up after themselves if they modify state
- [ ] No unrelated formatting or refactors in the same change
- [ ] Async handlers correctly use `async def` + `await`
