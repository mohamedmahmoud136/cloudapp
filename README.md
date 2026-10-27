# Data Storage & Sharing System

A lightweight Streamlit web application that lets you register data assets,
automatically determines a share level, suggests a storage method, and
provides useful statistics.

## ✨ Features

- **Add multiple records** with full validation (name, users, size, access type)
- **Automatic share level** — Individual, Team, Organization, or Large Scale
- **Storage method suggestion** — Local Storage, Shared Storage, or Cloud Storage
- **Per-record report cards** with colour-coded storage badges
- **Write-access warnings** for multi-user editable data
- **Global statistics** — total records, total size, largest record
- **Search** — exact match and partial-match suggestions
- **Export** — CSV for all records, `.txt` report per record
- **Sample data loader** and one-click "Clear all" control
- **Clean UI** with tabs, sidebar, and a neutral theme

## 🚀 Run Locally

```bash
# 1. Clone the repo
git clone https://github.com/mohamedmahmoud136/cloudapp.git
cd cloudapp

# 2. Create a virtual environment
python -m venv venv
# Windows PowerShell:
.\venv\Scripts\activate
# macOS / Linux:
# source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
```

The app opens in your browser at `http://localhost:8501`.

## ☁️ Deploy to Streamlit Community Cloud

1. Push this project to your GitHub repository (with `app.py` in the repo root).
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **Create app** → select your repo → branch `main` → main file `app.py`.
4. Click **Deploy** and wait for the build to finish.
5. The platform installs everything from `requirements.txt` automatically.
6. Once the build succeeds you get a public URL — verify it loads without errors.

## 🧪 Run Tests

```bash
pip install pytest
pytest tests/ -v
```

## 📁 Project Structure

```
cloudapp/
├── .gitignore
├── .streamlit/
│   └── config.toml          # theme configuration
├── app.py                   # Streamlit UI (presentation only)
├── logic.py                 # pure-Python business logic
├── requirements.txt         # pinned dependencies
├── README.md                # this file
└── tests/
    └── test_logic.py        # pytest unit tests
```
