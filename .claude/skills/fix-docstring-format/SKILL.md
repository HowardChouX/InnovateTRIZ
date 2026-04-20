---
name: fix-docstring-format
description: Use when asked to fix or normalize Python docstring formatting in the InnovateTRIZ codebase.
---

## Target Files

- `src/core/` - Core logic modules
- `src/ai/` - AI client modules
- `src/data/` - Data layer modules
- `src/ui/` - UI component modules
- `src/utils/` - Utility functions

## Docstring Conventions

### Single-line Docstring

```python
@dataclass
class MatrixResult:
    """Result of a TRIZ matrix query."""
    principles: List[int]
```

### Multi-line Docstring

```python
@dataclass
class MatrixResult:
    """Result of a TRIZ matrix query.

    Contains the recommended invention principles
    based on the contradiction parameters.

    Attributes:
        principles: List of principle numbers (1-40).
    """
```

### First Sentence Spanning Multiple Lines

Use `\` for line continuation:

```python
@dataclass
class MatrixResult:
    """Result of a TRIZ matrix query which could \
    span multiple lines in some cases."""
```

## Rules

1. First sentence should be concise and on one line if possible
2. Use `\` for line continuation in first sentence only
3. Every line should be at most 88 characters
4. If a line cannot be wrapped (e.g., long URL), add `# noqa: E501` to the closing `"""` line
5. Use Google style: `Args:`, `Returns:`, `Raises:` sections formatted correctly

## Examples

```python
# Wrong
@dataclass
class MyClass:
    property_a: str
    """
    Short description of a property.

    Full description.
    """

# Correct
@dataclass
class MyClass:
    property_a: str
    """Short description of a property."""

# Correct (first sentence spanning lines)
@dataclass
class MyClass:
    property_a: str
    """Short description of a property which could \
    take multiple lines."""
```

## Quality Checklist

- [ ] First sentence is complete and concise
- [ ] Line continuation uses `\` correctly
- [ ] No lines exceed 88 characters (unless unavoidable)
- [ ] Google-style sections formatted correctly
