"""Shared response helpers."""

from __future__ import annotations

from typing import Any


def success_response(data: Any = None, message: str = "Success") -> dict:
    """Uniform success envelope."""
    return {"status": "success", "message": message, "data": data}


def error_response(message: str = "An error occurred", errors: Any = None) -> dict:
    """Uniform error envelope."""
    return {"status": "error", "message": message, "errors": errors}
