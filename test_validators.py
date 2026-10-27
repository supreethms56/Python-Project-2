"""Tests 1 and 2: Unit tests for input validators."""

from decimal import Decimal
import pytest
from expense_tracker.validators import validate_amount, validate_date, validate_category


def test_amount_validation():
    """Test 1: The amount check accepts 450 and rejects -5, abc and an empty value."""
    # Valid amount
    assert validate_amount("450") == Decimal("450")
    assert validate_amount("450.50") == Decimal("450.50")

    # Rejection of negatives
    with pytest.raises(ValueError, match="positive number"):
        validate_amount("-5")

    # Rejection of non-numeric strings
    with pytest.raises(ValueError, match="valid number"):
        validate_amount("abc")

    # Rejection of empty value
    with pytest.raises(ValueError, match="cannot be empty"):
        validate_amount("")


def test_date_validation():
    """Test 2: The date check accepts 2026-10-01 and rejects 2026-13-40."""
    # Valid date
    assert validate_date("2026-10-01") == "2026-10-01"

    # Invalid calendar date
    with pytest.raises(ValueError, match="Invalid date"):
        validate_date("2026-13-40")

    # Empty date
    with pytest.raises(ValueError, match="cannot be empty"):
        validate_date("")
