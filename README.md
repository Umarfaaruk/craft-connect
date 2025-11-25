# Craft Connect 🎨

Craft Connect is a full-stack application designed to preserve and share cultural crafts. It connects a **Streamlit** frontend for user interaction with a robust **FastAPI** backend that proxies data to the Swecha Corpus API.

## 🚀 Tech Stack

* **Frontend:** Streamlit (Python) - Deployed on Streamlit Community Cloud
* **Backend:** FastAPI (Python) - Deployed on Render
* **Database/API:** Swecha Corpus API (External Service)
* **Authentication:** JWT Token-based authentication via phone number

## 📂 Project Structure

* `frontend/`: Contains the Streamlit user interface code.
* `backend/`: Contains the FastAPI service, API proxy logic, and authentication handlers.

## 🛠️ Setup & Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-gitlab-url>
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r backend/requirements.txt
    pip install -r frontend/requirements.txt
    ```

3.  **Run Locally:**
    * Backend: `uvicorn backend.main:app --reload`
    * Frontend: `streamlit run frontend/Home.py`
