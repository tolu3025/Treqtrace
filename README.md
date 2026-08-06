# TreqTrace — Software Validation System for Requirement Traceability

![TreqTrace Logo](static/images/logo.png)

> **Track. Trace. Validate.**

A web-based software validation system that supports effective requirement traceability and ensures that software requirements are properly tracked and validated throughout the Software Development Life Cycle (SDLC).

---

## Features

- **Requirement Management** — Capture, edit, version, and manage software requirements with full audit history
- **Traceability Engine** — Bidirectional linking between requirements, design artifacts, and test cases
- **Automated RTM** — Real-time Requirement Traceability Matrix generation
- **Validation Tracking** — Automatic detection of untested, failed, and validated requirements
- **Real-time Dashboard** — Visual overview of project health with charts and statistics
- **Report Generation** — Exportable CSV reports for traceability and validation status
- **Role-based Access** — Admin, Developer, and Tester roles with appropriate permissions
- **Version Control** — Full version history for every requirement change

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5, CSS3, JavaScript, Bootstrap 5, Chart.js |
| Backend | Python 3, Flask |
| Database | SQLite (default) / MySQL (production ready) |
| Authentication | Flask-Login with bcrypt password hashing |

---

## Quick Start

### 1. Install Dependencies

```bash
cd TreqTrace
pip install -r requirements.txt
```

### 2. Run the Application

```bash
python app.py
```

### 3. Access the Application

Open your browser and navigate to: **http://localhost:5000**

### 4. Default Login

- **Username:** `admin`
- **Password:** `admin123`

---

## Project Structure

```
TreqTrace/
├── app.py                  # Main Flask application
├── config.py               # Configuration settings
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── treqtrace.db            # SQLite database (auto-created)
├── static/
│   ├── css/
│   │   └── style.css       # Custom stylesheet
│   ├── js/
│   │   └── app.js          # Frontend scripts
│   └── images/
│       └── logo.png        # TreqTrace logo
└── templates/
    ├── base.html           # Base layout
    ├── landing.html        # Landing page
    ├── login.html          # Login page
    ├── register.html       # Registration page
    ├── dashboard.html      # Main dashboard
    ├── projects.html       # Project list
    ├── project_form.html   # New project form
    ├── project_detail.html # Project detail view
    ├── requirement_form.html
    ├── requirement_detail.html
    ├── design_form.html
    ├── test_form.html
    ├── traceability.html   # RTM view
    ├── reports.html        # Validation reports
    └── admin_users.html    # User management
```

---

## Database Schema

### Core Entities
- **Users** — Authentication and role management
- **Projects** — Top-level project containers
- **Requirements** — Software requirements with versioning
- **RequirementVersions** — Audit trail of requirement changes
- **DesignArtifacts** — Design components (diagrams, wireframes)
- **TestCases** — Test cases with execution status
- **TraceabilityLinks** — Bidirectional links between artifacts

---

## User Roles

| Role | Permissions |
|------|------------|
| **Admin** | Full access: manage users, all projects, all data |
| **Developer** | Create/manage projects, requirements, design artifacts |
| **Tester** | Create/manage test cases, update execution status |

---

## Switching to MySQL

To use MySQL instead of SQLite, update `config.py`:

```python
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://username:password@localhost/treqtrace'
```

Then install the MySQL driver:
```bash
pip install pymysql
```

---

## Author

**Oluwagbemiga Opemipo Stephen**  
Department of Software Engineering  
Faculty of Computing and Information Technology  
Osun State University, Osogbo, Nigeria

---

## License

This project was developed as a Final Year Project (FYP) for the award of BSc. Software Engineering.
"# Treqtrace" 
"# Treqtrace" 
"# Treqtrace" 
