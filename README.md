# Expense Tracker

A Flask web app for tracking personal income and expenses, with per-user accounts, categories, a dashboard of charts, CSV/Excel import and export, and a dark mode.

![Demo](https://github.com/GulmurodY/flask-expense-tracker/blob/main/expense-tracker-demo.gif)

## Features

- **Accounts**: sign up, log in and log out. Each user picks a currency at sign-up (USD, EUR, GBP, SAR, AED, RUB, TJS, UZS, KZT, CNY, JPY, INR, TRY), and amounts are shown with that currency's symbol.
- **Transactions**: add income or expense entries with an amount, category, comment and date. Future dates and negative amounts are rejected, and exactly one type must be chosen.
- **Categories**: Food, Transport, Housing, Shopping, Bills, Entertainment, Health, Salary and Other.
- **Transaction list**: paginated (10 per page), with income, expense and balance totals, a date-range filter, and a delete button on each row.
- **Dashboard**: balance, savings rate, top category and average expense, plus charts (built with Chart.js) for expenses by category, income vs. expense, and the monthly trend. A per-category breakdown shows each category's total, share of spending and number of transactions.
- **Import**: upload a `.csv` or `.xlsx` file with the columns `date, type, category, amount, currency, comment`. Only `amount` and `type` are required. Invalid rows are skipped and reported.
- **Export**: download transactions as `.csv` or `.xlsx`, respecting the current date filter, with a custom file name. Exported files can be imported back as-is. [`sample-expenses.xlsx`](sample-expenses.xlsx) is an example file.
- **Dark mode**: a toggle in the navigation bar. The choice is remembered in the browser.

## Getting started

Requires Python 3.11 or newer.

1. Clone the repository:

    ```bash
    git clone https://github.com/GulmurodY/flask-expense-tracker.git
    cd flask-expense-tracker
    ```

2. Install the dependencies (ideally in a virtual or conda environment):

    ```bash
    pip install -r requirements.txt
    ```

3. Optionally, create a `.env` file with a secret key for signing sessions. Without it, the app uses a development default.

    ```
    SECRET_KEY=your-random-secret
    ```

4. Run the app:

    ```bash
    python main.py
    ```

    Then open [http://localhost:8001](http://localhost:8001). Set the `PORT` environment variable to use a different port.

    On macOS/Linux, `./run.sh` activates the `expense_tracker` conda environment, starts the app, and frees the port when you stop it. `run.bat` does the same on Windows.

The SQLite database is created automatically at `instance/database.db` on first run.

## Project structure

```
main.py              Entry point
website/
  __init__.py        App factory, database setup and lightweight schema migrations
  auth.py            Sign-up, login and logout routes
  views.py           Transactions, dashboard, import, export and delete routes
  models.py          User and Note models, currencies and categories
  templates/         Jinja templates
  static/style.css   Styles, including the dark theme
docker/, kubernetes/ An older container and Kubernetes setup that hasn't been
                     updated for the current dependencies
```

## Built with

- **Flask**, with **Flask-SQLAlchemy** (SQLite) and **Flask-Login**
- **pandas** and **openpyxl** for import and export
- **Chart.js** for the dashboard charts
- **Bootstrap 4** and custom CSS for the interface
