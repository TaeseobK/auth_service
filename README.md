# AUTH Service

A Django-based **AUTH Service** that connects to multiple databases and integrates with external services for authentication and HR management. This service provides a structured API for consuming auth services.

---

## 📑 Table of Contents

1. [Introduction](#introduction)  
2. [Features](#features)  
3. [Architecture](#architecture)  
4. [Installation](#installation)  
5. [Configuration](#configuration)  
6. [Usage](#usage)  
7. [API Documentation](#api-documentation)  
8. [Database](#database)  
9. [Troubleshooting](#troubleshooting)  
10. [Contributors](#contributors)  
11. [License](#license)  

---

## 📖 Introduction

The **AUTH Service** is a backend API service built on **Django 5.2.5** and **Django REST Framework (DRF)**. It is designed to interact with finance-related databases while integrating authentication and HR data from external microservices.

---

## ✨ Features

- Built with **Django 5.2.5** and **Django REST Framework**.    
- Integration with **Fin Service** and **HR Service**.  
- **Custom Middlewares** for verifying authentication tokens and logout handling.  
- **API Documentation** generated automatically with `drf-spectacular`.  
- Token-based authentication via external Auth Service (`Authorization: Token <token>`).  
- Timezone support (`Asia/Jakarta`).  

---

## 🏛 Architecture

- **Framework:** Django (WSGI application)  
- **API Layer:** Django REST Framework (DRF)  
- **Documentation:** drf-spectacular + drf-spectacular-sidecar  
- **Authentication:** Delegated to external Auth Service (Token-based)  
- **Databases:**  
  - `default` → Authentication database  
- **Middleware:**  
  - `VerifyAuthTokenMiddleware` – validates tokens against Auth Service  
  - `AuthServiceLogoutMiddleware` – syncs logout events with Auth Service  

---

## ⚙️ Installation

### 1. Clone the repository
```bash
git clone https://github.com/your-repo/auth-service.git
cd fin-service
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate   # On Linux / Mac
venv\Scripts\activate      # On Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Apply database migrations
```bash
python manage.py migrate
```

### 5. Run the development server
```bash
python manage.py runserver
```

---

## 🔧 Configuration

Settings are split across two files:

- **`settings.py`** – Core Django settings.  
- **`local_settings.py`** – Environment-specific overrides (not committed).  

### Example `local_settings.py`
```python
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

AUTH_SERVICE = 'http://localhost:8000'
HR_SERVICE = 'http://localhost:8001'

DATABASE_SERVICE = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'databases/auth.sqlite3',
    },
    'fin_master': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'databases/fin_master.sqlite3',
    },
    'fin_dump': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'databases/fin_dump.sqlite3',
    }
}

DEBUG_ = True
```

### Key Configurable Options

| Setting        | Description                                        | Default                  |
|----------------|----------------------------------------------------|--------------------------|
| `AUTH_SERVICE` | URL of the external Auth microservice              | `http://localhost:8000` |
| `HR_SERVICE`   | URL of the external HR microservice                | `http://localhost:8001` |
| `DATABASES`    | Supports multiple databases (`default`, `fin_*`)   | SQLite local DBs         |
| `DEBUG_`       | Toggle for debug mode                              | `True`                   |
| `TIME_ZONE`    | Application timezone                               | `Asia/Jakarta`           |

---

## 🚀 Usage

### Authentication

All API requests must include a token issued by the **Auth Service**:

```http
Authorization: Token <your_token>
```

Custom middlewares validate these tokens before processing requests.

### Database Access

The service transparently routes queries to the correct database using **custom routers**:

- `fin_master` → Main finance data  
- `fin_dump` → Archived finance data  

---

## 📜 API Documentation

API documentation is available via **drf-spectacular**:

- OpenAPI schema:  
  ```
  /api/schema/
  ```
- Swagger UI (if configured):  
  ```
  /api/docs/
  ```

---

## 🗄 Database

This service supports **multiple databases** via Django’s database routers:

- `default` → Authentication database (`auth.sqlite3`)  
- `fin_master` → Primary finance database (`fin_master.sqlite3`)  
- `fin_dump` → Archived/dump finance database (`fin_dump.sqlite3`)  

You can switch to **PostgreSQL, MySQL, or other Django-supported backends** by editing `local_settings.py`.

---

## 🛠 Troubleshooting

- **Authentication Fails:** Ensure Auth Service is running and the token is included.  
- **Database Errors:** Verify paths to SQLite DBs or credentials for external DBs.  
- **API Docs Missing:** Check that `drf-spectacular` is installed and in `INSTALLED_APPS`.  
- **Logout Issues:** Confirm `AuthServiceLogoutMiddleware` is configured correctly.  

---

## 👥 Contributors

- **Satrio** – Initial Work & Maintenance.
- Contributions welcome via Pull Requests.  

---

## 📄 License

This project is licensed under the **UNLICENSE** – see the [LICENSE](LICENSE) file for details.
