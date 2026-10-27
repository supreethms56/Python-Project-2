"""CSV Export, Cleaning, Import, and Visualization tools."""

import csv
from datetime import datetime
from decimal import Decimal
import os
import re
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from expense_tracker.validators import (
    CATEGORY_MAP,
    VALID_CATEGORIES,
    paise_to_rupees,
    rupees_to_paise,
    validate_amount,
    validate_category,
    validate_date,
)
from expense_tracker.database import add_expense, exists_exact_expense, list_expenses


def export_to_csv(conn: sqlite3.Connection, output_path: str, month: Optional[str] = None, category: Optional[str] = None) -> int:
    """Export filtered expenses to a CSV file. Returns number of rows exported."""
    expenses = list_expenses(conn, month=month, category=category)
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    with open(output_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "date", "amount", "category", "note"])
        for exp in expenses:
            writer.writerow([exp["id"], exp["date"], f"{exp['amount']:.2f}", exp["category"], exp["note"]])

    return len(expenses)


def clean_row_data(row: Dict[str, str]) -> Tuple[Optional[str], Optional[Decimal], Optional[str], Optional[str], Optional[str]]:
    """Clean and validate a single CSV row.
    
    Returns (date, amount_decimal, category, note, rejection_reason).
    """
    raw_date = row.get("date", "").strip()
    raw_amount = row.get("amount", "").strip()
    raw_category = row.get("category", "").strip()
    raw_note = row.get("note", "").strip()

    # 1. Date cleaning: Accept MM-DD-YYYY, MM/DD/YYYY, and YYYY-MM-DD
    cleaned_date = None
    for fmt in ("%m-%d-%Y", "%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            dt = datetime.strptime(raw_date, fmt)
            cleaned_date = dt.strftime("%Y-%m-%d")
            break
        except ValueError:
            pass

    if not cleaned_date:
        return None, None, None, None, "invalid date"

    # 2. Amount cleaning: Strip currency symbols, commas, spaces
    cleaned_amt_str = re.sub(r"[₹$€, ]", "", raw_amount)
    if not cleaned_amt_str:
        return None, None, None, None, "invalid amount"

    try:
        amt_decimal = Decimal(cleaned_amt_str)
        if amt_decimal <= Decimal("0"):
            return None, None, None, None, "amount must be positive"
    except Exception:
        return None, None, None, None, "invalid amount"

    # 3. Category cleaning: case-insensitive match
    canonical_cat = CATEGORY_MAP.get(raw_category.lower())
    if not canonical_cat:
        return None, None, None, None, f"invalid category: {raw_category}"

    return cleaned_date, amt_decimal, canonical_cat, raw_note, None


def import_csv(conn: sqlite3.Connection, file_path: str, rejected_out_path: str = "output/rejected_rows.csv") -> Dict[str, Any]:
    """Import expenses from CSV with automated cleaning, deduplication, and rejected row logging."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File '{file_path}' does not exist.")

    imported_count = 0
    duplicates_count = 0
    rejected_rows: List[Tuple[Dict[str, str], str]] = []
    total_imported_paise = 0
    seen_in_batch = set()
    monthly_stats: Dict[str, Dict[str, Any]] = {}

    with open(file_path, mode="r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        reader.fieldnames = [name.strip().lower() for name in (reader.fieldnames or [])]

        for row in reader:
            cleaned_date, amt_dec, category, note, rejection = clean_row_data(row)

            if rejection:
                rejected_rows.append((row, rejection))
                continue

            amt_paise = rupees_to_paise(amt_dec)
            unique_key = (cleaned_date, amt_paise, category, note)

            if unique_key in seen_in_batch or exists_exact_expense(conn, amt_paise, cleaned_date, category, note):
                duplicates_count += 1
                continue

            seen_in_batch.add(unique_key)
            add_expense(conn, amt_paise, cleaned_date, category, note)
            imported_count += 1
            total_imported_paise += amt_paise

            # Track month statistics
            m_key = cleaned_date[:7]
            if m_key not in monthly_stats:
                monthly_stats[m_key] = {"count": 0, "paise": 0}
            monthly_stats[m_key]["count"] += 1
            monthly_stats[m_key]["paise"] += amt_paise

    if rejected_rows:
        os.makedirs(os.path.dirname(os.path.abspath(rejected_out_path)), exist_ok=True)
        with open(rejected_out_path, mode="w", newline="", encoding="utf-8") as f:
            fieldnames = ["date", "amount", "category", "note", "rejection_reason"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r, reason in rejected_rows:
                out_r = dict(r)
                out_r["rejection_reason"] = reason
                writer.writerow(out_r)

    return {
        "imported": imported_count,
        "duplicates": duplicates_count,
        "rejected": len(rejected_rows),
        "total_imported_amount": paise_to_rupees(total_imported_paise),
        "monthly_stats": {
            m: {"count": data["count"], "total": paise_to_rupees(data["paise"])}
            for m, data in sorted(monthly_stats.items())
        },
        "rejected_file": rejected_out_path if rejected_rows else None
    }


def save_spending_chart(conn: sqlite3.Connection, month_str: str, output_image_path: str = "output/chart.png") -> Optional[str]:
    """Generate a category spending bar chart using matplotlib (R11 stretch requirement)."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("⚠️  matplotlib is not installed. Run 'pip install matplotlib' to enable charting.")
        return None

    from expense_tracker.reports import generate_monthly_report
    report = generate_monthly_report(conn, month_str)

    if not report["breakdown"]:
        print(f"No expenses to plot for {month_str}.")
        return None

    categories = [b["category"] for b in report["breakdown"]]
    amounts = [float(b["total"]) for b in report["breakdown"]]

    os.makedirs(os.path.dirname(os.path.abspath(output_image_path)), exist_ok=True)

    plt.figure(figsize=(8, 5))
    bars = plt.bar(categories, amounts, color="#3b82f6", edgecolor="#1d4ed8")
    plt.title(f"Spending by Category - {month_str}", fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Category", fontsize=11, fontweight="bold")
    plt.ylabel("Total Spent (₹)", fontsize=11, fontweight="bold")
    plt.grid(axis="y", linestyle="--", alpha=0.6)

    for bar in bars:
        height = bar.get_height()
        plt.annotate(f"₹{height:,.0f}",
                     xy=(bar.get_x() + bar.get_width() / 2, height),
                     xytext=(0, 4),
                     textcoords="offset points",
                     ha="center", va="bottom", fontsize=9, fontweight="bold")

    plt.tight_layout()
    plt.savefig(output_image_path, dpi=300)
    plt.close()
    return output_image_path
