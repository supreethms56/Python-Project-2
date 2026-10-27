# 💰 Smart Expense Tracker

A modular command-line application written in Python to track personal expenses, categorize spending, generate breakdown reports, export/import CSV records with automated deduplication and cleaning, and plot visual monthly expense charts.

---

## 📑 Table of Contents

- [Features](#-features)
- [Project Structure](#-project-structure)
- [Requirements](#-requirements)
- [Installation & Setup](#-installation--setup)
- [Usage & Commands](#-usage--commands)
  - [1. Add an Expense (`add`)](#1-add-an-expense-add)
  - [2. List Expenses (`list`)](#2-list-expenses-list)
  - [3. Edit an Expense (`edit`)](#3-edit-an-expense-edit)
  - [4. Delete an Expense (`delete`)](#4-delete-an-expense-delete)
  - [5. Monthly Report (`report`)](#5-monthly-report-report)
  - [6. Export to CSV (`export`)](#6-export-to-csv-export)
  - [7. Import from CSV (`import`)](#7-import-from-csv-import)
  - [8. Generate Spending Chart (`chart`)](#8-generate-spending-chart-chart)
  - [Custom Database Flag (`--db`)](#custom-database-flag---db)
- [Validation & Categories](#-validation--categories)

---

## ✨ Features

- **Accurate Financial Calculations:** Internally stores amounts as integer paise (`amount_paise`) to prevent floating-point inaccuracies.
- **Robust Input Validation:** Strict parsing and format normalizations for amounts, dates, and categories.
- **SQLite Storage:** Light and portable file-based storage with parameterized queries.
- **Flexible Date Display:** Normalizes dates into standard storage formats while presenting clean, user-friendly views.
- **CSV Import with Data Cleaning:** Automatically strips currency symbols (`₹`, `$`, `€`), handles date variations, catches duplicates, and routes malformed rows to an error log.
- **Visual Analytics:** Generates monthly category distribution bar charts using Matplotlib.

---

## 🗂 Project Structure

```text
.
├── expense_tracker/          # Core package directory
│   ├── __init__.py           # Package initializer
│   ├── cli.py                # Command Line Interface (argparse & command handlers)
│   ├── csv_tools.py          # CSV import/export, data sanitization, and Matplotlib chart generator
│   ├── database.py           # SQLite connection, table migrations, and CRUD operations
│   ├── reports.py            # Aggregations, percentage breakdown, and text report formatting
│   └── validators.py         # Input parsing, canonical category mapping, and currency conversion
├── output/                   # Default directory for CSV exports, reports, and charts
├── expenses.db               # Default SQLite database file (created automatically)
└── README.md
```

---

## ⚙️ Requirements

- **Python 3.8+**
- **Matplotlib** *(optional, required only for the `chart` command)*

---

## 🚀 Installation & Setup

### 1. Clone or Open the Repository
Navigate to the root directory where the project resides:
```bash
cd smart-expense-tracker
```

### 2. Set Up a Virtual Environment (Recommended)
```bash
# On macOS / Linux:
python3 -m venv venv
source venv/bin/activate

# On Windows:
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
If you plan to generate visual charts (`chart` command), install `matplotlib`:
```bash
pip install matplotlib
```

*(No additional external packages are needed for core functionality; SQLite and standard Python modules are used.)*

### 4. Running the Tool
You can invoke the CLI directly using the Python module syntax:
```bash
python -m expense_tracker.cli --help
```

*(Tip: If you add an entry point script or run setup, you can also wrap this as a `tracker` or `expense` shell alias.)*

---

## 📖 Usage & Commands

### Global Flag: Custom Database (`--db`)
By default, data is stored in `expenses.db`. To use a custom SQLite file, pass `--db <path>` before any subcommand:
```bash
python -m expense_tracker.cli --db my_test_expenses.db list
```

---

### 1. Add an Expense (`add`)
Adds an individual expense record.

```bash
python -m expense_tracker.cli add --amount <AMOUNT> --date <DATE> --category <CATEGORY> [--note "<NOTE>"]
```

- `--amount`: Positive number (e.g. `450` or `1250.75`).
- `--date`: Date formatted as `MM-DD-YYYY`, `MM/DD/YYYY`, or `YYYY-MM-DD`.
- `--category`: One of `Food`, `Rent`, `Travel`, `Bills`, `Shopping`, `Other` (case-insensitive).
- `--note`: Optional brief description.

**Example:**
```bash
python -m expense_tracker.cli add --amount 450.50 --date 10-22-2026 --category Food --note "Team Lunch"
```

---

### 2. List Expenses (`list`)
Displays a tabular list of stored expenses.

```bash
python -m expense_tracker.cli list [--month YYYY-MM] [--category CATEGORY]
```

**Examples:**
```bash
# List all expenses:
python -m expense_tracker.cli list

# Filter by month (October 2026):
python -m expense_tracker.cli list --month 2026-10

# Filter by category:
python -m expense_tracker.cli list --category Travel
```

---

### 3. Edit an Expense (`edit`)
Update any field of an existing expense by specifying its `ID`.

```bash
python -m expense_tracker.cli edit <ID> [--amount <AMOUNT>] [--date <DATE>] [--category <CATEGORY>] [--note "<NOTE>"]
```

**Example:**
```bash
python -m expense_tracker.cli edit 3 --amount 600 --note "Client Dinner"
```

---

### 4. Delete an Expense (`delete`)
Deletes an expense by its unique `ID`.

```bash
python -m expense_tracker.cli delete <ID>
```

**Example:**
```bash
python -m expense_tracker.cli delete 3
```

---

### 5. Monthly Report (`report`)
Generates an aggregated summary and breakdown per category sorted from highest to lowest expenditure.

```bash
python -m expense_tracker.cli report --month YYYY-MM
```

**Example:**
```bash
python -m expense_tracker.cli report --month 2026-10
```

**Sample Output:**
```text
October 2026 report by category (highest first):

  Category    Total        Share
  Rent        25,000.00    58.1%
  Food         9,500.00    22.1%
  Bills        5,000.00    11.6%
  Travel       3,500.00     8.1%
```

---

### 6. Export to CSV (`export`)
Exports records to a CSV file. Supports month and category filters.

```bash
python -m expense_tracker.cli export [--month YYYY-MM] [--category CATEGORY] [--out PATH]
```

**Examples:**
```bash
# Export all records (defaults to output/expenses.csv):
python -m expense_tracker.cli export

# Export specific month to custom file:
python -m expense_tracker.cli export --month 2026-10 --out backups/oct_2026.csv
```

---

### 7. Import from CSV (`import`)
Imports records from a CSV file. Automatically parses amounts (handling currency marks like `₹`, `$`), strips whitespace, validates dates/categories, rejects malformed rows, and skips duplicates.

```bash
python -m expense_tracker.cli import --file <CSV_PATH> [--rejected <REJECTED_CSV_PATH>]
```

- `--file`: Path to the source CSV file containing `date`, `amount`, `category`, and optional `note` columns.
- `--rejected`: Path to log skipped/invalid rows (defaults to `output/rejected_rows.csv`).

**Example:**
```bash
python -m expense_tracker.cli import --file imports/bank_statement.csv
```

---

### 8. Generate Spending Chart (`chart`)
Plots a category-wise bar chart for the chosen month and saves it as an image.

```bash
python -m expense_tracker.cli chart --month YYYY-MM [--out PATH]
```

- `--month`: Format `YYYY-MM`.
- `--out`: Destination image file (defaults to `output/chart_YYYY-MM.png`).

**Example:**
```bash
python -m expense_tracker.cli chart --month 2026-10 --out output/october_spending.png
```

---

## 🛡️ Validation & Categories

- **Allowed Categories:**
  - `Food`
  - `Rent`
  - `Travel`
  - `Bills`
  - `Shopping`
  - `Other`
  *(Inputs are case-insensitive, e.g. `food` or `FOOD` will automatically map to `Food`)*.
- **Accepted Date Formats:** `MM-DD-YYYY`, `MM/DD/YYYY`, `YYYY-MM-DD`, `DD-MM-YYYY`, `DD/MM/YYYY`.
- **Amounts:** Must be strictly positive values (`> 0`).