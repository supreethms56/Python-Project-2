"""Monthly summary and category breakdown reporting."""

from datetime import datetime
from decimal import Decimal
import sqlite3
from typing import Any, Dict, List
from expense_tracker.validators import paise_to_rupees, validate_month


def generate_monthly_report(conn: sqlite3.Connection, month_str: str) -> Dict[str, Any]:
    """Generate total spending, expense count, and category breakdown for a given month."""
    norm_month = validate_month(month_str)

    # Total and count query
    summary_query = """
    SELECT COUNT(*) as total_count, COALESCE(SUM(amount_paise), 0) as total_paise
    FROM expenses
    WHERE expense_date LIKE ?;
    """
    cur = conn.execute(summary_query, (f"{norm_month}-%",))
    summary_row = cur.fetchone()
    total_count = summary_row["total_count"]
    total_paise = summary_row["total_paise"]
    total_amount = paise_to_rupees(total_paise)

    # Category breakdown query ordered highest total first
    cat_query = """
    SELECT category, COUNT(*) as cat_count, SUM(amount_paise) as cat_paise
    FROM expenses
    WHERE expense_date LIKE ?
    GROUP BY category
    ORDER BY cat_paise DESC;
    """
    cur = conn.execute(cat_query, (f"{norm_month}-%",))
    cat_rows = cur.fetchall()

    breakdown: List[Dict[str, Any]] = []
    for r in cat_rows:
        c_amt = paise_to_rupees(r["cat_paise"])
        share = (Decimal(r["cat_paise"]) / Decimal(total_paise) * Decimal("100")) if total_paise > 0 else Decimal("0.0")
        breakdown.append({
            "category": r["category"],
            "count": r["cat_count"],
            "total": c_amt,
            "share": float(share)
        })

    return {
        "month": norm_month,
        "total_amount": total_amount,
        "total_count": total_count,
        "breakdown": breakdown
    }


def format_report_text(report: Dict[str, Any]) -> str:
    """Format the report matching the exact expected output style."""
    dt = datetime.strptime(report["month"], "%Y-%m")
    month_title = dt.strftime("%B %Y")

    lines = []
    lines.append(f"\n{month_title} report by category (highest first):\n")

    if report["total_count"] == 0:
        lines.append("  No expenses found for this month.\n")
        return "\n".join(lines)

    lines.append("  Category    Total        Share")
    for item in report["breakdown"]:
        cat = item["category"]
        total = f"{item['total']:,.2f}"
        share = f"{item['share']:.1f}%"
        lines.append(f"  {cat:<10}  {total:>9}    {share:>5}")

    lines.append("")
    return "\n".join(lines)
