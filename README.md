# 💊 Medicine Schedule Reminder System

A modern, full-stack healthcare web application designed to help patients manage daily prescription medications, receive real-time audio and browser reminders, track dose adherence, and view daily and weekly schedules.

---

## 🌟 Key Features

1. **Home / Landing Page (`index.html`)**
   - Premium medical landing page with project introduction, live adherence statistics, and quick navigation.
2. **User Registration & Secure Authentication (`register.html`, `login.html`, `logout.html`)**
   - User account registration with form validation and password encryption using bcrypt.
   - Secure JWT Bearer token authentication with 7-day persistent session management.
   - Complete multi-tenant privacy: each user can only see and manage their own medication records.
3. **Interactive Healthcare Dashboard (`dashboard.html`)**
   - Patient greeting with dynamic adherence rate indicator.
   - 4 live summary cards: Total Medicines, Today's Scheduled Doses, Completed Doses, and Pending Doses.
   - Quick action dose logger ("Mark as Taken" or "Skip Dose") directly from the dashboard.
4. **Add Medicine Page (`add_medicine.html`)**
   - Complete medication input: name, dosage, form (Tablet, Capsule, Syrup, Drops, Inhaler, etc.), frequency (Once Daily, Twice Daily, Three Times Daily), reminder timings, meal association (Before Food, After Food, With Food), and doctor instructions.
5. **Medicine List Page (`medicine_list.html`)**
   - Complete catalog of prescribed medications.
   - Live debounced search filter.
   - Edit modal dialog to update dosage, timings, or instructions without page reload.
   - One-click deletion with confirmation.
6. **Medication Schedule Page (`schedule.html`)**
   - **Daily Schedule:** Segmented into Morning (05:00 - 11:59), Afternoon (12:00 - 16:59), Evening (17:00 - 20:59), and Night (21:00 - 04:59).
   - **Weekly Matrix:** Monday through Sunday overview.
   - Date picker to inspect past or future medication schedules.
7. **Reminders & Alert Center (`reminders.html`)**
   - Real-time dose tracker polling every 15 seconds.
   - Native browser desktop notifications with permission toggle.
   - Built-in two-tone medical audio chime using the HTML5 Web Audio API (no external MP3 required).
   - Duplicate alert prevention.
8. **Adherence History Page (`history.html`)**
   - Permanent log of taken, skipped, and missed medications.
   - Filter by status and date.
   - Precise action timestamps.
9. **Patient Profile (`profile.html`)**
   - View profile details, update name and contact number, and change password securely.

---

## 🛠️ Technology Stack

- **Frontend:** HTML5, CSS3, Vanilla JavaScript (ES6+), Inter Font, Custom Healthcare Responsive UI.
- **Backend:** Python 3.11+, FastAPI, Uvicorn, SQLAlchemy 2.0, Pydantic v2, PyJWT, Passlib / Bcrypt.
- **Database:** MySQL / MariaDB (Database name: `medicine_reminder_db`).

---

## 📁 Project Structure

```
project medicine/
│
├── frontend/
│   ├── index.html            # Landing / Home Page
│   ├── login.html            # Login Page (preserves original design)
│   ├── register.html         # User Registration Page
│   ├── dashboard.html        # Main Healthcare Dashboard
│   ├── add_medicine.html     # Add New Prescription Medicine
│   ├── medicine_list.html    # Manage, Search, Edit & Delete Medicines
│   ├── schedule.html         # Daily & Weekly Schedule Matrix
│   ├── reminders.html        # Live Audio & Push Reminder Alerts
│   ├── history.html          # Medication Adherence History & Logs
│   ├── profile.html          # Patient Profile & Password Change
│   ├── logout.html           # Safe Session Logout
│   ├── css/
│   │   └── style.css         # Modern Medical CSS Theme
│   ├── js/
│   │   └── api.js            # Unified API Client, Auth & Audio Chime
│   └── assets/               # Media & Icons
│
├── backend/
│   ├── main.py               # FastAPI App & REST Endpoints
│   ├── database.py           # SQLAlchemy Connection & Engine
│   ├── models.py             # SQLAlchemy ORM Models
│   ├── schemas.py            # Pydantic Request/Response Models
│   ├── auth.py               # JWT Token Generation & Bcrypt Hashing
│   ├── routes/
│   │   ├── __init__.py
│   │   └── auth_routes.py    # Authentication & Profile Endpoints
│   └── requirements.txt      # Python Dependencies
│
├── database/
│   └── medicine_reminder.sql # MySQL Database Schema
│
└── README.md
```

---

## 🚀 Step-by-Step Setup & Execution

### Step 1: Start MySQL Database
Ensure MySQL (or XAMPP MySQL) is running on port `3306`:
- If using XAMPP, open the XAMPP Control Panel and start **MySQL**.
- Alternatively, launch from terminal:
  ```powershell
  D:\xampp\mysql\bin\mysqld.exe --defaults-file="D:\xampp\mysql\bin\my.ini" --console
  ```

### Step 2: Create Database & Tables
The database schema has already been pre-configured in `medicine_reminder_db`. To re-import if needed:
```powershell
Get-Content "C:\Users\MY PC\Desktop\project medicine\database\medicine_reminder.sql" | & "D:\xampp\mysql\bin\mysql.exe" -u root
```

### Step 3: Install Python Dependencies
Open PowerShell in the `backend` folder and run:
```powershell
cd "C:\Users\MY PC\Desktop\project medicine\backend"
python -m pip install -r requirements.txt
```

### Step 4: Run FastAPI Server
Start the FastAPI backend with uvicorn:
```powershell
cd "C:\Users\MY PC\Desktop\project medicine\backend"
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

The interactive Swagger API documentation will be available at:
👉 **http://127.0.0.1:8000/docs**

### Step 5: Open the Application in Browser
You can open the web application in any of the following two ways:
1. **Directly via the FastAPI Server (Recommended):**
   Open your browser and navigate to:
   👉 **http://127.0.0.1:8000/**
2. **Directly via VS Code / File Explorer:**
   Right-click `frontend/index.html` or `frontend/login.html` and choose **Open with Live Server** or double click to open in any web browser.

---

## 🧪 Testing Account Credentials

You can create any new account on the registration page, or use the following pre-tested account:
- **Email:** `patient@example.com`
- **Password:** `password123`

---

## 🔒 Security & Data Isolation
- Passwords are encrypted with 12 rounds of bcrypt.
- All private endpoints require a valid JWT Bearer token.
- SQL queries strictly filter by `current_user.id`, preventing cross-tenant data leaks.
