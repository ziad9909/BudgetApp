# Personal Budgeting System

A Django web application for tracking income and expenses, setting category budgets, managing savings goals, and monitoring recurring subscriptions in one dashboard.

## Features

- User authentication and profile-based data isolation
- Add and manage income and expense transactions
- Set monthly category budgets with progress alerts
- Track savings goals and completion status
- Manage recurring subscriptions and due checks
- Notification system for important budget events

## Tech Stack

- Python 3.x
- Django
- SQLite (default local database)

## Project Structure

- `budget/` main application logic (models, views, templates, routes)
- `budgeting_project/` Django project settings and root URLs
- `manage.py` Django command entry point
- `requirements.txt` Python dependencies

## Local Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Apply migrations:

```bash
python manage.py migrate
```

4. Run the development server:

```bash
python manage.py runserver
```

5. Open:

```text
http://127.0.0.1:8000/
```

## Notes

- The default database file is `db.sqlite3`.
- Make sure migrations are applied before first use.
