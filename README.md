# Craft Connect

**Preserving Traditional Crafts & Cultural Heritage**

Craft Connect is a web application developed in collaboration with [Swecha](https://swecha.org/) to document and preserve traditional crafts for future generations.

---

## Architecture

```
┌──────────────────┐      ┌──────────────────────┐      ┌───────────────────────────┐
│  Streamlit       │      │  FastAPI Backend      │      │  Swecha Corpus API        │
│  Frontend        │─────▶│  (proxy server)       │─────▶│  api.corpus.swecha.org    │
│  Port 8501       │ HTTP │  Port 8000            │ HTTP │                           │
└──────────────────┘      └──────────────────────┘      └───────────────────────────┘
```

| Component | Tech | Purpose |
|-----------|------|---------|
| **Frontend** | Streamlit (Python) | UI — Home, Share Craft, Community Gallery |
| **Backend** | FastAPI + Uvicorn | Proxy API — auth, uploads, fetching records |
| **External API** | Swecha Corpus API | Data store — users, records, categories |

---

## Project Structure

```
craft-connect/
├── backend/
│   ├── .env                     # Environment variables (API base URL)
│   ├── main.py                  # FastAPI app — endpoints & middleware
│   ├── requirements.txt         # Python dependencies
│   ├── start.bat / start.sh     # Startup scripts (Windows / Linux)
│   └── services/
│       ├── __init__.py
│       └── corpus_service.py    # All Corpus API communication logic
│
└── frontend/
    ├── .streamlit/
    │   ├── config.toml          # Streamlit config (upload limits)
    │   └── secrets.toml         # Backend URL (override for deployment)
    ├── Home.py                  # Landing page
    ├── utils.py                 # Shared UI components (header, sign-out)
    ├── requirements.txt         # Python dependencies
    └── pages/
        ├── 1_Share_Craft.py     # Auth + upload form
        └── _Community_Gallery.py # Gallery grid view
```

---

## Getting Started

### Prerequisites
- Python 3.10+
- pip

### 1. Set up the backend

```bash
cd backend

# Create virtual environment (first time only)
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### 2. Set up the frontend

```bash
cd frontend

# Install dependencies (in the same or a separate venv)
pip install -r requirements.txt

# Start Streamlit
streamlit run Home.py
```

### 3. Open the app

Visit **[Craft Connect](https://craft-connect.streamlit.app/)** in your browser.

---

## Configuration

| Variable | File | Default | Description |
|----------|------|---------|-------------|
| `SWECHA_API_BASE_URL` | `backend/.env` | `https://api.corpus.swecha.org` | Base URL of the Corpus API |
| `BACKEND_URL` | `frontend/.streamlit/secrets.toml` | `http://127.0.0.1:8000` | URL of the FastAPI backend |

---

## Features

- **User Authentication** — Sign in / sign up via phone number and password
- **Craft Upload** — Upload images and videos (up to 1 GB) with descriptions
- **Community Gallery** — Browse all shared crafts in a responsive 3-column grid
- **Category Support** — Crafts are categorised using the Corpus API's category system

---

## License

This project is developed as part of the Swecha initiative for preserving cultural heritage.
