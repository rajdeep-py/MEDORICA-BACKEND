# Medorica Backend (FastAPI)

This backend is built with FastAPI and PostgreSQL.

## Prerequisites

- macOS
- Python 3.10+
- PostgreSQL running locally (or remote DB access)

## 1) Open project folder

```bash
cd /Users/rajdeepdey/Documents/Medorica/medorica_backend
```

## 2) Create virtual environment

```bash
python3 -m venv venv
```

## 3) Activate virtual environment

```bash
source venv/bin/activate
```

You should now see `(venv)` in your terminal.

## 4) Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 5) Configure environment variables

Edit `.env` and set your DB values:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=medorica_db
DB_USER=your_postgres_user
DB_PASSWORD=your_postgres_password

CORS_ORIGINS=*
PORT=8000
```

Optional (if you prefer one URL):

```env
DATABASE_URL=postgresql+psycopg2://your_postgres_user:your_postgres_password@localhost:5432/medorica_db
```

## 6) Run backend server

### Option A: Run with Python

```bash
python main.py
```

### Option B: Run with Uvicorn

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 7) Verify server is running

- Healthcheck: `http://127.0.0.1:8000/health`
- Swagger UI: `http://127.0.0.1:8000/docs`

## 8) Stop and deactivate

- Stop server: `Ctrl + C`
- Deactivate venv:

```bash
deactivate
```

