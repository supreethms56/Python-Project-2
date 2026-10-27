"""Validation logic for expense tracking inputs."""

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional, Tuple

VALID_CATEGORIES = ["Food", "Rent", "Travel", "Bills", "Shopping", "Other"]
CATEGORY_MAP = {c.lower(): c for c in VALID_CATEGORIES}


def validate_amount(amount_str: str) -> Decimal:
    """Validate that amount is a non-empty positive number.
    
    Returns Decimal representation in rupees.
    Raises ValueError with user-friendly message on failure.
    """
    if amount_str is None:
        raise ValueError("Amount cannot be empty.")
    
    cleaned = str(amount_str).strip()
    if not cleaned:
        raise ValueError("Amount cannot be empty.")
    
    try:
        amount = Decimal(cleaned)
    except (InvalidOperation, TypeError):
        raise ValueError(f"Invalid amount '{amount_str}'. Must be a valid number.")
    
    if amount <= Decimal("0"):
        raise ValueError("Amount must be a positive number greater than 0.")
    
    return amount


def validate_date(date_str: str) -> str:
    """Validate date and normalize to YYYY-MM-DD for database storage.
    
    Accepts:
      - MM-DD-YYYY (e.g., 10-22-2026)
      - MM/DD/YYYY (e.g., 10/22/2026)
      - YYYY-MM-DD (e.g., 2026-10-22)
    """
    if not date_str or not str(date_str).strip():
        raise ValueError("Date cannot be empty. Expected MM-DD-YYYY.")

    cleaned = str(date_str).strip()

    accepted_formats = [
        "%m-%d-%Y",  # MM-DD-YYYY (e.g. 10-22-2026)
        "%m/%d/%Y",  # MM/DD/YYYY (e.g. 10/22/2026)
        "%Y-%m-%d",  # ISO standard
        "%d-%m-%Y",
        "%d/%m/%Y",
    ]

    for fmt in accepted_formats:
        try:
            dt = datetime.strptime(cleaned, fmt)
            return dt.strftime("%Y-%m-%d")  # Stored internally as YYYY-MM-DD
        except ValueError:
            continue

    raise ValueError(f"Invalid date '{date_str}'. Expected valid date in MM-DD-YYYY format.")


def validate_category(category_str: str) -> str:
    """Validate category against the fixed allowed list (case-insensitive).
    
    Returns canonical category string.
    Raises ValueError with user-friendly message on failure.
    """
    if not category_str or not str(category_str).strip():
        raise ValueError(f"Category cannot be empty. Must be one of: {', '.join(VALID_CATEGORIES)}.")
    
    cleaned = str(category_str).strip().lower()
    canonical = CATEGORY_MAP.get(cleaned)
    if not canonical:
        raise ValueError(f"Invalid category '{category_str}'. Allowed categories: {', '.join(VALID_CATEGORIES)}.")
    
    return canonical


def validate_month(month_str: str) -> str:
    """Validate month string format YYYY-MM."""
    if not month_str or not str(month_str).strip():
        raise ValueError("Month cannot be empty. Expected YYYY-MM.")
    
    cleaned = str(month_str).strip()
    try:
        dt = datetime.strptime(cleaned, "%Y-%m")
        return dt.strftime("%Y-%m")
    except ValueError:
        raise ValueError(f"Invalid month '{month_str}'. Expected format YYYY-MM (e.g., 2026-10).")


def rupees_to_paise(rupees: Decimal) -> int:
    """Convert rupee Decimal to integer paise safely without floating-point errors."""
    return int((rupees * 100).to_integral_value())


def paise_to_rupees(paise: int) -> Decimal:
    """Convert integer paise back to rupee Decimal."""
    return (Decimal(paise) / Decimal("100")).quantize(Decimal("0.01"))
