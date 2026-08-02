# Decore — Construction Management Dashboard

A Django starter project for a single Civil Engineer / Contractor to manage
employees, worksites, attendance, salaries, payments, materials and expenses.

> **Phase 1 — Structure only.** This is a scaffold: professional Bootstrap 5
> UI, reusable templates, navigation and placeholder pages. No models, CRUD,
> database relationships, forms, business logic, salary/profit calculations,
> report logic, or APIs have been implemented yet. Every placeholder file
> contains `TODO` comments marking where real logic belongs in a future phase.

---

## Tech Stack

- **Backend:** Python 3, Django 6 (latest stable)
- **Frontend:** HTML5, Bootstrap 5, Bootstrap Icons, JavaScript, Chart.js
- **Database:** SQLite

## Project Structure

```
decore/
├── manage.py
├── requirements.txt
├── README.md
├── db.sqlite3               (created after migrate)
├── decore/                  # Project settings package
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── accounts/                 # Login / logout (Engineer & Supervisor roles)
├── dashboard/                 # Dashboard home page
├── employees/                 # Employee list / form / detail
├── worksites/                 # Worksite list / form / detail
├── attendance/                 # Attendance list / form
├── salaries/                   # Salary list
├── payments/                   # Payment list
├── materials/                  # Material list
├── expenses/                   # Expense list
├── reports/                    # Reports page
├── settings/                   # App settings page
├── templates/
│   ├── base.html
│   ├── includes/
│   │   ├── navbar.html
│   │   ├── sidebar.html
│   │   └── footer.html
│   └── <app>/...              # Per-app templates
├── static/
│   ├── css/style.css
│   ├── js/app.js
│   └── images/
└── media/
```

Each app contains the standard Django files: `apps.py`, `admin.py`,
`urls.py`, `views.py`, `models.py`, `tests.py`, `__init__.py`. `models.py`
and `views.py` are placeholders with `TODO` comments — `views.py` currently
renders each page with Django's generic `TemplateView` so the UI is fully
browsable with no data wired up yet.

## Getting Started

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser   # optional, for /admin/
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` — it redirects to the Dashboard.

To view the placeholder login page, visit `http://127.0.0.1:8000/accounts/login/`.
All app pages (Dashboard, Employees, Worksites, Attendance, Salaries,
Payments, Materials, Expenses, Reports, Settings) currently require a
logged-in user (`LoginRequiredMixin`) — create a superuser with
`python manage.py createsuperuser` and log in to browse them, or remove
`LoginRequiredMixin` temporarily while developing Phase 1 UI.

## Roles

Two user roles are referenced in the UI (login page role selector, profile
labels): **Engineer** and **Supervisor**. No role-based permission logic is
implemented in Phase 1 — this is UI-only scaffolding for a future phase.

## What's Included

- ✅ Django project structure with 11 apps
- ✅ Bootstrap 5 responsive UI (sidebar + top navbar layout)
- ✅ Reusable `base.html`, navbar, sidebar and footer includes
- ✅ Dashboard with stat cards, Chart.js placeholder charts, and a recent
  activity table
- ✅ List / form / detail placeholder pages for every module
- ✅ Search bars, pagination controls, toasts, loading spinner and a shared
  confirmation modal (UI only)
- ✅ Dark mode toggle (UI only)
- ✅ Static file structure (`css/`, `js/`, `images/`) and `media/` folder

## What's NOT Included (by design — future phases)

- ❌ Models / database relationships
- ❌ CRUD operations
- ❌ Django Forms tied to models
- ❌ Salary or profit calculation logic
- ❌ Report generation logic
- ❌ APIs
- ❌ Authentication / role-permission logic

## Theme

| Token       | Value      |
|-------------|------------|
| Primary     | `#1E3A8A`  |
| Secondary   | `#F59E0B`  |
| Background  | `#F8FAFC`  |
| Cards       | White, subtle shadow |
