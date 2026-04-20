---
name: fix-members-short-description
description: Use when asked to fix short descriptions of Python type members.
---

## Target Files

Python modules in specified file or directory.

## Background

Documentation generators use the first sentence of a member docstring as the short description.

## Convention

### Correct Format

```python
@dataclass
class MyControl:
    property_a: str
    """
    Short description of a property.

    Full description.
    Another line of full description.
    """
```

### First Sentence Spanning Multiple Lines

Use `\` for line continuation:

```python
@dataclass
class MyControl:
    property_a: str
    """
    Short description of a property which could \
    take multiple lines.

    Full description.
    Another line of full description.
    """
```

## Task

Traverse all types (classes, enums, etc.) in the input file or directory and ensure the first sentence of their docstrings uses `\` correctly for line continuation.

Apply the fix regardless of whether the first sentence starts on the same line as `"""` or on a following line.

## Character Limit

Ensure every docstring line is at most 88 characters (including any trailing `\`).

If a line contains unbreakable content (e.g., long URL or Windows registry path like `HKEY_LOCAL_MACHINE\\...`), add `# noqa: E501` to the closing `"""` line instead of the long line.

## Examples

```python
# Wrong
@dataclass
class MatrixResult:
    """Result of a TRIZ matrix query which could take multiple lines.
    Full description here."""

# Correct
@dataclass
class MatrixResult:
    """Result of a TRIZ matrix query which could \
    take multiple lines.
    Full description here."""
```

## Scope

- `src/core/` - All types in core modules
- `src/ai/` - All types in AI modules
- `src/data/` - All types in data modules
- `src/ui/` - All types in UI modules
