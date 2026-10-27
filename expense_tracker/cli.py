"""Command Line Interface for Smart Expense Tracker."""

import argparse
import sys
from expense_tracker.database import (
    add_expense,
    delete_expense,
    get_connection,
    get_expense,
    init_db,
    list_expenses,
    update_expense,
)
from expense_tracker.validators import (
    rupees_to_paise,
    validate_amount,
    validate_category,
    validate_date,
    validate_month,
)
from expense_tracker.reports import format_report_text, generate_monthly_report
from expense_tracker.csv_tools import export_to_csv, import_csv, save_spending_chart


def print_table(expenses):
    """Format and print expenses list with dates shown as MM-DD-YYYY."""
    if not expenses:
        print("📭 No expenses found matching your criteria.")
        return

    from datetime import datetime

    print("\n" + "=" * 76)
    print(f"{'ID':<5} {'Date (MM-DD-YYYY)':<20} {'Category':<12} {'Amount (₹)':>12}  {'Note':<25}")
    print("-" * 76)
    for exp in expenses:
        # Convert YYYY-MM-DD from database to MM-DD-YYYY for terminal view
        try:
            display_date = datetime.strptime(exp['date'], "%Y-%m-%d").strftime("%m-%d-%Y")
        except Exception:
            display_date = exp['date']

        note = (exp['note'][:22] + "...") if len(exp['note']) > 25 else exp['note']
        print(f"{exp['id']:<5} {display_date:<20} {exp['category']:<12} {exp['amount']:>12,.2f}  {note:<25}")
    print("=" * 76 + "\n")


def handle_add(args, conn):
    amt = validate_amount(args.amount)
    dt = validate_date(args.date)
    cat = validate_category(args.category)
    paise = rupees_to_paise(amt)

    exp_id = add_expense(conn, paise, dt, cat, args.note)
    print(f"✅ Added expense #{exp_id}: ₹{amt:,.2f} on {dt} [{cat}] ('{args.note or ""}')")


def handle_list(args, conn):
    month = validate_month(args.month) if args.month else None
    cat = validate_category(args.category) if args.category else None
    expenses = list_expenses(conn, month=month, category=cat)
    print_table(expenses)


def handle_edit(args, conn):
    existing = get_expense(conn, args.id)
    if not existing:
        print(f"❌ Error: Expense with ID #{args.id} does not exist.")
        return

    updates = {}
    if args.amount is not None:
        amt = validate_amount(args.amount)
        updates["amount_paise"] = rupees_to_paise(amt)
    if args.date is not None:
        updates["expense_date"] = validate_date(args.date)
    if args.category is not None:
        updates["category"] = validate_category(args.category)
    if args.note is not None:
        updates["note"] = args.note

    if not updates:
        print("⚠️  No fields provided to update.")
        return

    update_expense(conn, args.id, **updates)
    updated = get_expense(conn, args.id)
    print(f"✨ Successfully updated expense #{args.id}:")
    print(f"   Date: {updated['date']} | Category: {updated['category']} | Amount: ₹{updated['amount']:,.2f} | Note: {updated['note']}")


def handle_delete(args, conn):
    if delete_expense(conn, args.id):
        print(f"🗑️  Successfully deleted expense #{args.id}.")
    else:
        print(f"❌ Error: Expense with ID #{args.id} does not exist.")


def handle_report(args, conn):
    month = validate_month(args.month)
    report = generate_monthly_report(conn, month)
    print(format_report_text(report))


def handle_export(args, conn):
    month = validate_month(args.month) if args.month else None
    cat = validate_category(args.category) if args.category else None
    out_file = args.out or f"output/expenses_{month or 'all'}.csv"
    count = export_to_csv(conn, out_file, month=month, category=cat)
    print(f"📁 Successfully exported {count} expenses to '{out_file}'.")


def handle_import(args, conn):
    res = import_csv(conn, args.file, args.rejected or "output/rejected_rows.csv")
    print(f"\n  Total rows loaded:        {res['imported']}")
    
    # Print per-month totals like 'September 2026: 3 expenses, total 16,219.00'
    for month_key, stats in res.get("monthly_stats", {}).items():
        from datetime import datetime
        m_name = datetime.strptime(month_key, "%Y-%m").strftime("%B %Y")
        print(f"  {m_name + ':':<26}{stats['count']} expenses, total {stats['total']:,.2f}")

    if res['duplicates'] > 0:
        print(f"  Duplicates skipped:       {res['duplicates']}")
    if res['rejected'] > 0:
        print(f"  Rows rejected:            {res['rejected']}")
        if res['rejected_file']:
            print(f"  Rejected details saved to: {res['rejected_file']}")
    print("")


def handle_chart(args, conn):
    month = validate_month(args.month)
    out_path = args.out or f"output/chart_{month}.png"
    saved = save_spending_chart(conn, month, out_path)
    if saved:
        print(f"📈 Chart successfully generated and saved to '{saved}'")


def build_parser():
    parser = argparse.ArgumentParser(
        prog="expense_tracker",
        description="Smart Expense Tracker: CLI tool to track spending, view breakdowns, and export/import data."
    )
    parser.add_argument("--db", default="expenses.db", help="Path to SQLite database file (default: expenses.db)")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # add
    p_add = subparsers.add_parser("add", help="Add a new expense")
    p_add.add_argument("--amount", required=True, help="Expense amount (e.g. 450 or 450.50)")
    p_add.add_argument("--date", required=True, help="Expense date YYYY-MM-DD")
    p_add.add_argument("--category", required=True, help="Category (Food, Rent, Travel, Bills, Shopping, Other)")
    p_add.add_argument("--note", default="", help="Optional note/description")

    # list
    p_list = subparsers.add_parser("list", help="List expenses (newest first)")
    p_list.add_argument("--month", help="Filter by month (YYYY-MM)")
    p_list.add_argument("--category", help="Filter by category")

    # edit
    p_edit = subparsers.add_parser("edit", help="Edit an existing expense by ID")
    p_edit.add_argument("id", type=int, help="Expense ID to edit")
    p_edit.add_argument("--amount", help="New amount")
    p_edit.add_argument("--date", help="New date YYYY-MM-DD")
    p_edit.add_argument("--category", help="New category")
    p_edit.add_argument("--note", help="New note")

    # delete
    p_del = subparsers.add_parser("delete", help="Delete an expense by ID")
    p_del.add_argument("id", type=int, help="Expense ID to delete")

    # report
    p_rep = subparsers.add_parser("report", help="Generate monthly spending report")
    p_rep.add_argument("--month", required=True, help="Month to report on (YYYY-MM)")

    # export
    p_exp = subparsers.add_parser("export", help="Export expenses to CSV")
    p_exp.add_argument("--month", help="Filter export by month (YYYY-MM)")
    p_exp.add_argument("--category", help="Filter export by category")
    p_exp.add_argument("--out", default="output/expenses.csv", help="Output file path (default: output/expenses.csv)")

    # import (stretch)
    p_imp = subparsers.add_parser("import", help="Import expenses from CSV with cleaning (Stretch)")
    p_imp.add_argument("--file", required=True, help="Path to CSV file to import")
    p_imp.add_argument("--rejected", default="output/rejected_rows.csv", help="Path to write rejected rows")

    # chart (stretch)
    p_chart = subparsers.add_parser("chart", help="Save monthly spending chart as PNG (Stretch)")
    p_chart.add_argument("--month", required=True, help="Month to chart (YYYY-MM)")
    p_chart.add_argument("--out", help="Output image path")

    return parser


def run():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    conn = get_connection(args.db)
    init_db(conn)

    handlers = {
        "add": handle_add,
        "list": handle_list,
        "edit": handle_edit,
        "delete": handle_delete,
        "report": handle_report,
        "export": handle_export,
        "import": handle_import,
        "chart": handle_chart,
    }

    try:
        handlers[args.command](args, conn)
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
    finally:
        conn.close()
