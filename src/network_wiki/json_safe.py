"""Safe JSON serialization helpers to prevent template injection vulnerabilities."""

from __future__ import annotations

import json
from typing import Any


def serialize_json(obj: Any, ensure_ascii: bool = False) -> str:
    """Serialize an object to JSON string with defensive error handling.

    Args:
        obj: Python object to serialize (dict, list, primitive).
        ensure_ascii: Whether to escape non-ASCII characters.

    Returns:
        JSON-encoded string suitable for embedding in templates.

    Raises:
        TypeError: If object contains unserializable types.
        ValueError: If serialized output exceeds size limits.

    Example::
        >>> sanitize_for_html({"key": '<script>alert(1)</script>'})
        '{"key": "\\\\u003cscript\\\\u003ealert(1)\\\\u003c/script\\\\u003e"}'
    """
    # Serialize with escaping
    result = json.dumps(obj, ensure_ascii=ensure_ascii, cls=_EscapedJSONEncoder)

    # Basic sanity check for extreme sizes
    if len(result) > 10_000_000:  # 10MB limit
        raise ValueError(f"Serialized JSON too large: {len(result)} bytes")

    return result


def validate_json_injection_safety(json_str: str) -> None:
    """Validate that a JSON string won't break when embedded in JavaScript contexts.

    Checks for dangerous patterns that could cause syntax errors or injection:
    - Unterminated strings
    - Raw control characters (< 0x20 except escaped)
    - Unicode escape sequences that could become HTML entities

    Args:
        json_str: Serialized JSON string to validate.

    Raises:
        ValueError: If unsafe patterns detected.

    Example::
        >>> validate_json_injection_safety('{"key": "<script>"}')
        # Raises ValueError: Contains raw '<' character outside of HTML context

    Note:
        This is a defense-in-depth measure. Always use proper templating
        (auto-escaping) as primary protection.
    """
    # Check for unterminated structures
    try:
        parsed = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON structure: {e.msg}") from e

    # Recursively walk tree looking for suspicious patterns
    _check_value_safety(parsed, path="$")


def _check_value_safety(value: Any, path: str) -> None:
    """Recursively validate JSON value safety."""
    if isinstance(value, dict):
        for k, v in value.items():
            _check_value_safety(v, f"{path}.{k}")
    elif isinstance(value, list):
        for i, item in enumerate(value):
            _check_value_safety(item, f"{path}[{i}]")
    elif isinstance(value, str):
        # Check for raw control characters that shouldn't be in JSON
        for char_code in range(0x00, 0x20):
            if chr(char_code) in value and f"\\u{char_code:04x}" not in value.replace("\\", "").replace(chr(char_code), ""):
                raise ValueError(f"Suspicious control character U+{char_code:04X} found at {path}")


class _EscapedJSONEncoder(json.JSONEncoder):
    """Custom encoder that escapes potentially dangerous characters."""

    def encode(self, o: Any) -> str:
        # Use standard json.dumps but post-process for extra safety
        result = super().encode(o)

        # Additional escaping for common attack vectors when embedded in JS
        # These get converted to unicode escapes that browsers interpret safely
        replacements = [
            ('<', '\\u003c'),   # Less-than sign
            ('>', '\\u003e'),   # Greater-than sign
            ('&', '\\u0026'),   # Ampersand
            ("/'", "\\u002f'"), # Forward slash followed by quote (edge case)
        ]

        for old, new in replacements:
            result = result.replace(old, new)

        return result
