"""SQLite database layer for Smart Expense Tracker."""

import sqlite3
from typing import Any, Dict, List, Optional
from expense_tracker.validators import paise_to_rupees

DEFAULT_DB_PATH = "expenses.db"


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Create and return an SQLite connection with Row factory enabled."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Initialize the expenses table schema if not already present."""
    query = """
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        amount_paise INTEGER NOT NULL CHECK (amount_paise > 0),
        expense_date TEXT NOT NULL,
        category TEXT NOT NULL,
        note TEXT
    );
    """
    with conn:
        conn.execute(query)


def add_expense(conn: sqlite3.Connection, amount_paise: int, expense_date: str, category: str, note: Optional[str] = None) -> int:
    """Insert a new expense into database using parameterized query. Returns new ID."""
    query = """
    INSERT INTO expenses (amount_paise, expense_date, category, note)
    VALUES (?, ?, ?, ?);
    """
    with conn:
        cursor = conn.execute(query, (amount_paise, expense_date, category, note or ""))
        return cursor.lastrowid


def get_expense(conn: sqlite3.Connection, expense_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a single expense by ID."""
    query = "SELECT id, amount_paise, expense_date, category, note FROM expenses WHERE id = ?;"
    cursor = conn.execute(query, (expense_id,))
    row = cursor.fetchone()
    if not row:
        return None
    return {
        "id": row["id"],
        "amount": paise_to_rupees(row["amount_paise"]),
        "amount_paise": row["amount_paise"],
        "date": row["expense_date"],
        "category": row["category"],
        "note": row["note"]
    }


def list_expenses(conn: sqlite3.Connection, month: Optional[str] = None, category: Optional[str] = None) -> List[Dict[str, Any]]:
    """List expenses ordered by date descending (newest first), with optional month and category filters."""
    conditions = []
    params: List[Any] = []

    if month:
        conditions.append("expense_date LIKE ?")
        params.append(f"{month}-%")

    if category:
        conditions.append("category = ?")
        params.append(category)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    query = f"""
    SELECT id, amount_paise, expense_date, category, note
    FROM expenses
    {where_clause}
    ORDER BY expense_date ASC, id ASC;
    """
    cursor = conn.execute(query, tuple(params))
    rows = cursor.fetchall()
    return [
        {
            "id": r["id"],
            "amount": paise_to_rupees(r["amount_paise"]),
            "amount_paise": r["amount_paise"],
            "date": r["expense_date"],
            "category": r["category"],
            "note": r["note"]
        }
        for r in rows
    ]


def update_expense(conn: sqlite3.Connection, expense_id: int, **fields: Any) -> bool:
    """Update specific fields of an expense by ID."""
    valid_db_fields = {"amount_paise", "expense_date", "category", "note"}
    updates = []
    params: List[Any] = []

    for k, v in fields.items():
        if k in valid_db_fields and v is not None:
            updates.append(f"{k} = ?")
            params.append(v)

    if not updates:
        return False

    params.append(expense_id)
    query = f"UPDATE expenses SET {', '.join(updates)} WHERE id = ?;"
    with conn:
        cursor = conn.execute(query, tuple(params))
        return cursor.rowcount > 0


def delete_expense(conn: sqlite3.Connection, expense_id: int) -> bool:
    """Delete an expense by ID. Returns True if found and deleted, False otherwise."""
    query = "DELETE FROM expenses WHERE id = ?;"
    with conn:
        cursor = conn.execute(query, (expense_id,))
        return cursor.rowcount > 0


def exists_exact_expense(conn: sqlite3.Connection, amount_paise: int, expense_date: str, category: str, note: Optional[str]) -> bool:
    """Check if an identical expense already exists in the database for duplicate detection."""
    query = """
    SELECT 1 FROM expenses 
    WHERE amount_paise = ? AND expense_date = ? AND category = ? AND note = ?
    LIMIT 1;
    """
    cursor = conn.execute(query, (amount_paise, expense_date, category, note or ""))
    return cursor.fetchone() is not None
