# P35 DevFolio — Developer Portfolio Builder

SEPM academic demonstration: Flask + SQLite + HTML/CSS. Features: profile editor, 3 themes, projects CRUD (add/delete), skills CRUD (add/delete), public portfolio, local contact messages, dashboard, health and metrics APIs. Uses rule-based input validation, not a trained AI model. No email sending, authentication, production hosting, or analytics service is implemented.

## Windows PowerShell
```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```
Open http://127.0.0.1:5000. New terminal for tests:
```powershell
.\.venv\Scripts\python.exe -m pytest -v
.\.venv\Scripts\python.exe -m pytest --cov=app --cov-report=html --cov-report=term-missing
start htmlcov\index.html
```

All demo information is synthetic. The SQLite database is generated locally and ignored by Git.
