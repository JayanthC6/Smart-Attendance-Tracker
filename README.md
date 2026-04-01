# Smart Attendance Tracker

A Flask-based web application to manage student attendance with role-based access for admins, faculty, and students.

## Features

- Role-based login (admin, faculty, student)
- Student registration
- Course management
- Attendance marking and tracking
- Attendance summaries for students

## Tech Stack

- Python
- Flask
- SQLite
- HTML/CSS templates (Jinja2)

## Project Structure

```text
Smart-Attendance-Tracker/
├── app.py
├── database.py
├── models.py
├── requirements.txt
├── templates/
├── static/
└── tests/
```

## Setup

1. Clone the repository and move into the project directory.
2. (Recommended) Create and activate a virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Initialize the database:

```bash
python database.py
```

5. Start the app:

```bash
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

## Default Admin Login (Development Only)

When `database.py` is used to initialize the database, it creates a default admin user:

- Username: `admin`
- Password: `admin123`

⚠️ This is for local development only. Change the default password immediately before any shared or production use.

## Tests

Run tests with:

```bash
# Install pytest if needed
pip install pytest

python -m pytest tests/
```
