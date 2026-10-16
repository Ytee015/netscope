# NETSCOPE — IT Help Desk & Assets Management System

NETSCOPE is a Flask-based IT support and asset management platform with separate dashboards for administrators, staff, and technicians.

## Features

- Secure authentication with Flask-Login
- Role-based access control
- Asset inventory management
- Staff ticket creation and tracking
- Technician assignment and ticket status updates
- Maintenance logging
- Database-driven dashboards and reports
- SQLite persistence via SQLAlchemy

## Python requirements

- Python 3.10 or newer
- A virtual environment is recommended

## Windows setup

1. Open PowerShell in the project folder
2. Create a virtual environment:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
3. Install dependencies:
   ```powershell
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```
4. Copy and configure environment variables:
   ```powershell
   Copy-Item .env.example .env
   ```
   Then update `.env` with your preferred secret:
   ```env
   SECRET_KEY=replace-with-a-secure-secret-key
   DATABASE_URL=sqlite:///instance/netscope.db
   FLASK_ENV=development
   ```
5. Initialize the database:
   ```powershell
   flask --app run.py init-db
   ```
6. Create the first administrator:
   ```powershell
   flask --app run.py create-admin --username admin --email admin@example.com --password StrongPassword123
   ```
7. Start the application:
   ```powershell
   python run.py
   ```
8. Open:
   ```text
   http://127.0.0.1:5000
   ```

## Linux/macOS setup

1. Open a terminal in the project folder
2. Create a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```
4. Configure environment variables:
   ```bash
   cp .env.example .env
   ```
   Update `.env` as needed.
5. Initialize the database:
   ```bash
   flask --app run.py init-db
   ```
6. Create the first administrator:
   ```bash
   flask --app run.py create-admin --username admin --email admin@example.com --password StrongPassword123
   ```
7. Start the app:
   ```bash
   python run.py
   ```
8. Open:
   ```text
   http://127.0.0.1:5000
   ```

## Logging in

- Log into the application with the username or email of the administrator you created.
- Staff accounts can be created through the public registration page.
- Technician accounts can be added by an administrator from the user management page.

## Default workflow

1. Log in as the admin.
2. Create staff and technician accounts.
3. Add assets.
4. Assign assets to staff members.
5. Staff create maintenance requests as tickets.
6. Administrators assign tickets to technicians.
7. Technicians update ticket statuses and log maintenance activity.

## Tests

Run the test suite with:

```bash
python -m pytest -q
```

## Notes

- The SQLite database is stored in `instance/netscope.db`.
- Do not commit `.env` or production database files to source control.
- The database is not reset automatically on app startup.
