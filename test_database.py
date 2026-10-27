"""Tests 3, 4, and 5: Database operations on in-memory SQLite."""

from decimal import Decimal
import pytest
from expense_tracker.database import (
    add_expense,
    delete_expense,
    get_connection,
    get_expense,
    init_db,
    list_expenses,
)
from expense_tracker.validators import rupees_to_paise
from expense_tracker.reports import generate_monthly_report


@pytest.fixture
def db_conn():
    """Fixture providing a clean in-memory database connection for each test."""
    conn = get_connection(":memory:")
    init_db(conn)
    yield conn
    conn.close()


def test_add_and_read_expense(db_conn):
    """Test 3: An added expense can be read back with the same values."""
    paise = rupees_to_paise(Decimal("450.50"))
    exp_id = add_expense(db_conn, paise, "2026-10-22", "Food", "Team lunch")

    item = get_expense(db_conn, exp_id)
    assert item is not None
    assert item["id"] == exp_id
    assert item["amount"] == Decimal("450.50")
    assert item["date"] == "2026-10-22"
    assert item["category"] == "Food"
    assert item["note"] == "Team lunch"


def test_delete_expense(db_conn):
    """Test 4: Deleting one expense leaves the others untouched."""
    id1 = add_expense(db_conn, rupees_to_paise(Decimal("100")), "2026-10-01", "Food", "Snack")
    id2 = add_expense(db_conn, rupees_to_paise(Decimal("200")), "2026-10-02", "Travel", "Metro")
    id3 = add_expense(db_conn, rupees_to_paise(Decimal("300")), "2026-10-03", "Bills", "Internet")

    # Delete middle expense
    success = delete_expense(db_conn, id2)
    assert success is True

    # Check that deleted is gone
    assert get_expense(db_conn, id2) is None

    # Check that other two remain untouched
    remaining = list_expenses(db_conn)
    remaining_ids = [r["id"] for r in remaining]
    assert id1 in remaining_ids
    assert id3 in remaining_ids
    assert len(remaining) == 2


def test_monthly_total_aggregation(db_conn):
    """Test 5: The monthly total equals sum of that month's expenses and ignores other months."""
    # Add expenses in October 2026
    add_expense(db_conn, rupees_to_paise(Decimal("1000.00")), "2026-10-01", "Rent", "Oct advance")
    add_expense(db_conn, rupees_to_paise(Decimal("450.50")), "2026-10-15", "Food", "Groceries")

    # Add expense in September 2026 (must be ignored)
    add_expense(db_conn, rupees_to_paise(Decimal("5000.00")), "2026-09-30", "Bills", "Old bill")

    report = generate_monthly_report(db_conn, "2026-10")

    # Check October total is exactly 1000.00 + 450.50 = 1450.50
    assert report["total_count"] == 2
    assert report["total_amount"] == Decimal("1450.50")
