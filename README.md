# 🚑 GOLDENROUTE: A GOLDEN HOUR-AWARE INTELLIGENT EMERGENCY ROUTING AND HEALTHCARE RESOURCE OPTIMIZATION

GoldenRoute is a Django-based web application designed to optimize emergency medical response. 
It intelligently routes ambulances to the best available hospital in real time, taking into account ER availability, ICU beds, required specialist presence,
and live travel time via the OpenRouteService API. The platform also allows citizens to send distress signals that are automatically dispatched 
to the nearest ambulance.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Tech Stack](#tech-stack)
3. [Architecture & Project Structure](#architecture--project-structure)
4. [Data Models](#data-models)
5. [User Roles & Dashboards](#user-roles--dashboards)
6. [Core Features](#core-features)
7. [Hospital Scoring Algorithm](#hospital-scoring-algorithm)
8. [API Integrations](#api-integrations)
9. [URL Routes](#url-routes)
10. [Database](#database)
11. [How to Run the Project](#how-to-run-the-project)

---

## Project Overview

GoldenRoute solves a critical problem in emergency healthcare: **which hospital should an ambulance go to?**

When an ambulance responds to an emergency, the driver needs to quickly decide which hospital is best — not just the closest, but the one that has:
- Available ER rooms and ICU beds
- The right specialist on duty (cardiologist, neurosurgeon, trauma team)
- The shortest real-world travel time

GoldenRoute automates this decision with a weighted scoring algorithm and live routing data. It also enables citizens 
to trigger a distress signal from their dashboard, which gets routed to the nearest available ambulance.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend Framework | Django 5.x |
| API Layer | Django REST Framework |
| Database | SQLite3 (file-based, included) |
| Routing API | OpenRouteService API v2 |
| Navigation | Google Maps (deep-link integration) |
| Templating | Django Templates (server-side HTML) |
| Language | Python 3.11 |

---

## Architecture & Project Structure

```
goldenroute/                        ← Root Django project folder
│
├── manage.py                       ← Django management CLI entry point
├── db.sqlite3                      ← SQLite database (pre-seeded)
│
├── goldenroute/                    ← Django project config package
│   ├── settings.py                 ← App settings, DB config, installed apps
│   ├── urls.py                     ← Root URL dispatcher
│   ├── wsgi.py                     ← WSGI server entry point
│   └── asgi.py                     ← ASGI server entry point
│
└── core/                           ← Main application
    ├── models.py                   ← All database models
    ├── views.py                    ← Business logic & request handling
    ├── urls.py                     ← App-level URL patterns
    ├── admin.py                    ← Django admin registrations
    ├── utils.py                    ← Scoring algorithm & routing API client
    ├── serializers.py              ← DRF serializers (for API use)
    ├── tests.py                    ← Unit test stubs
    │
    ├── migrations/                 ← Database schema migrations (0001–0016)
    │
    └── templates/
        ├── base.html               ← Shared HTML layout
        └── core/
            ├── login.html
            ├── citizen_signup.html
            ├── citizen_dashboard.html
            ├── edit_health_profile.html
            ├── ambulance_dashboard.html
            └── hospital_dashboard.html
```

---

## Data Models

### `UserProfile`
Extends Django's built-in `User` model with a role and real-time GPS location.

| Field | Type | Description |
|---|---|---|
| `user` | OneToOneField (User) | Link to Django auth user |
| `role` | CharField | One of: `ambulance`, `hospital`, `citizen` |
| `latitude` | FloatField | Current GPS latitude |
| `longitude` | FloatField | Current GPS longitude |
| `location_updated_at` | DateTimeField | Timestamp of last location update |

---

### `HealthProfile`
Stores a citizen's medical identity and health history for use during emergencies.

| Field | Type | Description |
|---|---|---|
| `user` | OneToOneField (User) | Link to citizen's login account |
| `name` | CharField | Full name |
| `aadhar_number` | CharField (unique) | 12-digit national ID number |
| `comments` | TextField | Doctor notes / medical history |
| `age` | IntegerField | Age |
| `blood_group` | CharField | e.g., `O+`, `AB-` |
| `diabetes` | BooleanField | Diabetic flag |
| `heart_disease` | BooleanField | Heart disease flag |
| `emergency_contact` | CharField | Phone number of next-of-kin |

---

### `Hospital`
Represents a hospital with live resource availability and geographic coordinates.

| Field | Type | Description |
|---|---|---|
| `user` | OneToOneField (User) | Hospital staff login account |
| `name` | CharField | Hospital name |
| `er_rooms_available` | IntegerField | Current free ER rooms |
| `icu_beds_available` | IntegerField | Current free ICU beds |
| `cardiologist_available` | BooleanField | Cardiologist on duty |
| `neurosurgeon_available` | BooleanField | Neurosurgeon on duty |
| `trauma_team_available` | BooleanField | Trauma team on duty |
| `latitude` / `longitude` | FloatField | Hospital GPS location |
| `last_updated` | DateTimeField | Auto-updated on save |

---

### `EmergencyCase`
A record of an ambulance dispatch event linking an ambulance driver to a hospital.

| Field | Type | Description |
|---|---|---|
| `patient_type` | CharField | `cardiac`, `neuro`, or `trauma` |
| `ambulance_user` | ForeignKey (User) | Ambulance driver who handled the case |
| `selected_hospital` | ForeignKey (Hospital) | Hospital chosen for transport |
| `created_at` | DateTimeField | Auto-set on creation |

---

### `PatientTransfer`
A confirmed transfer record sent to the hospital with full patient and ETA details.

| Field | Type | Description |
|---|---|---|
| `hospital` | ForeignKey (Hospital) | Receiving hospital |
| `citizen` | ForeignKey (HealthProfile) | Patient being transferred |
| `ambulance_user` | ForeignKey (User) | Driver making the transfer |
| `patient_type` | CharField | Emergency type |
| `eta_minutes` | FloatField | Estimated arrival time in minutes |
| `sent_time` | DateTimeField | When the transfer was confirmed |

---

### `TrafficInput`
Manual or calculated travel time data between a case and a hospital.

| Field | Type | Description |
|---|---|---|
| `case` | ForeignKey (EmergencyCase) | Associated emergency case |
| `hospital` | ForeignKey (Hospital) | Candidate hospital |
| `travel_time_minutes` | FloatField | Travel time in minutes |

---

### `DistressSignal`
A citizen-triggered SOS signal auto-assigned to the nearest ambulance.

| Field | Type | Description |
|---|---|---|
| `citizen` | ForeignKey (HealthProfile) | Who sent the signal |
| `latitude` / `longitude` | FloatField | Citizen's GPS location |
| `assigned_ambulance` | ForeignKey (User) | Nearest ambulance auto-assigned |
| `emergency_phone` | CharField | Citizen's emergency contact phone |
| `created_at` | DateTimeField | Signal creation time |

---

## User Roles & Dashboards

GoldenRoute has three distinct user roles, each with its own dashboard and access scope.

### 🚑 Ambulance Driver
- Updates their real-time GPS location
- Enters patient type (cardiac / neuro / trauma) and their own coordinates
- Sees the best-scored hospital recommendation with ETA
- Confirms transport — which notifies the hospital and creates a PatientTransfer record
- Views distress signals assigned to them, with a direct Google Maps navigation link to the citizen

### 🏥 Hospital
- Views current ER room and ICU bed counts
- Toggles specialist availability (Cardiologist, Neurosurgeon, Trauma Team)
- Updates their status via a form (reflected immediately in the routing algorithm)
- Sees a live list of incoming patients with full medical details, specialist needed, ETA, and timestamp

### 👤 Citizen
- Registers an account and fills in their health profile (Aadhaar, blood group, conditions, emergency contact)
- Sends a distress signal with their GPS coordinates
- The system auto-finds the nearest ambulance and assigns the distress signal to them

---

## Core Features

**Smart Hospital Routing** — When an ambulance searches for hospitals, GoldenRoute filters out any hospital with zero ER rooms, zero ICU beds,
or a missing required specialist. For qualifying hospitals it queries OpenRouteService for real driving time and scores each using the weighted 
algorithm described below.

**Distress Signal System** — Citizens can trigger an SOS from their dashboard. The system scans all ambulance UserProfiles with stored coordinates,
computes Euclidean distance to each, and assigns the signal to the nearest one. The ambulance driver sees the citizen's name, Aadhaar, phone number,
location, and a one-click Google Maps navigation link.

**Patient Pre-Notification** — When an ambulance confirms a hospital, a `PatientTransfer` record is created. The hospital dashboard immediately displays
the incoming patient's full medical profile (age, blood group, diabetes, heart disease status, emergency contact, specialist required, and ETA), 
allowing staff to prepare in advance.

**Role-Based Access Control** — Login redirects users to their appropriate dashboard based on their role. Dashboard views enforce role checks and
redirect unauthorized users back to login.

**Session Memory** — After a citizen edits their health profile, their name and Aadhaar are stored in the session so the ambulance dashboard
can pre-populate the Aadhaar field for quick lookups.

**Admin Panel** — All models (Hospital, EmergencyCase, TrafficInput, HealthProfile, PatientTransfer, UserProfile) are registered with Django Admin
for superuser management.

---

## Hospital Scoring Algorithm

Defined in `core/utils.py → calculate_hospital_score()`.

```
Score = (ER rooms × 3)
      + (ICU beds × 2)
      + (Specialist match ? +20 : -20)
      - (Travel time in minutes × 1.5)
```

The hospital with the highest score is recommended as `best_hospital`. This balances resource availability against proximity — a far hospital with
many resources can still beat a nearby hospital that lacks a specialist or has no ICU beds.

---

## API Integrations

### OpenRouteService (Routing)
Used in `core/utils.py → get_travel_time()`.

- **Endpoint:** `POST https://api.openrouteservice.org/v2/directions/driving-car`
- **Auth:** Bearer token in the `Authorization` header (configured as `API_KEY` in `utils.py`)
- **Input:** Ambulance coordinates and hospital coordinates
- **Returns:** Duration in seconds and distance in meters, converted to minutes and km
- **Fallback:** Returns `None` on API error; that hospital is skipped in scoring

### Google Maps (Navigation deep-link)
Used in the ambulance dashboard template. When a distress signal is displayed, a pre-built Google Maps URL is generated with the ambulance's current 
coordinates as the origin and the citizen's signal coordinates as the destination. No API key is required for this — it is a standard Maps URL redirect.

---

## URL Routes

| URL | View | Name | Role |
|---|---|---|---|
| `/` | `login_view` | `home` | All |
| `/login/` | `login_view` | `login` | All |
| `/citizen-signup/` | `citizen_signup` | `citizen_signup` | Public |
| `/citizen/` | `citizen_dashboard` | `citizen_dashboard` | Citizen |
| `/edit-profile/` | `edit_health_profile` | `edit_health_profile` | Citizen |
| `/distress/` | `distress_signal` | `distress_signal` | Citizen |
| `/ambulance/` | `ambulance_dashboard` | `ambulance_dashboard` | Ambulance |
| `/hospital/` | `hospital_dashboard` | `hospital_dashboard` | Hospital |
| `/admin/` | Django Admin | — | Superuser |

---

## Database

The project ships with a pre-seeded `db.sqlite3` file. All 16 migrations are already applied. You can use the existing database as-is or 
reset it and create fresh data via the admin panel.

---

## How to Run the Project

### Prerequisites

Make sure the following are installed on your system:

- Python 3.11 or later
- pip (Python package manager)
- Git (optional, if cloning)

---

### Step 1 — Extract the Project

Unzip the project archive and navigate into the project root:

```bash
unzip goldenroute_fulllll_.zip
cd goldenroute
```

---

### Step 2 — Create a Virtual Environment

```bash
python -m venv venv
```

Activate it:

**On macOS / Linux:**
```bash
source venv/bin/activate
```

**On Windows:**
```bash
venv\Scripts\activate
```

---

### Step 3 — Install Dependencies

There is no `requirements.txt` in the zip, but the project needs the following packages. Install them:

```bash
pip install django djangorestframework requests
```

Full dependency list:

| Package | Purpose |
|---|---|
| `django` | Core web framework |
| `djangorestframework` | REST API support |
| `requests` | HTTP calls to OpenRouteService API |

---

### Step 4 — Configure API Keys

Open `core/utils.py` and verify or replace the OpenRouteService API key:

```python
API_KEY = "your_openrouteservice_api_key_here"
```

Get a free key at: https://openrouteservice.org/dev/#/signup

> **Note:** The project ships with an existing key in `utils.py`. If it has expired or hit its quota, replace it with your own.

Also open `goldenroute/settings.py` and update the Google Maps placeholder if needed:

```python
GOOGLE_MAPS_API_KEY = "YOUR_API_KEY"
```

> The Google Maps key is currently only used for navigation deep-links (no JS Maps embed), so this setting can be left as-is for local development.

---

### Step 5 — Apply Migrations

The database is pre-seeded and migrations are already applied. If you are starting fresh or on a clean system, run:

```bash
python manage.py migrate
```

---

### Step 6 — Create a Superuser (Optional)

If you want to access the Django admin panel to create hospitals, ambulance accounts, or manage data:

```bash
python manage.py createsuperuser
```

Follow the prompts to set a username, email, and password.

---

### Step 7 — Run the Development Server

```bash
python manage.py runserver
```

The app will be available at: **http://127.0.0.1:8000/**

---

### Step 8 — Set Up Test Accounts via Admin

Go to **http://127.0.0.1:8000/admin/** and log in with your superuser credentials.

To test the full flow, create the following:

**1. A Hospital account:**
- Create a `User` (e.g., username: `city_hospital`, password: `test1234`)
- Create a `UserProfile` linked to that user with role = `hospital`
- Create a `Hospital` record linked to that user with a name, ER rooms, ICU beds, specialist flags, and latitude/longitude

**2. An Ambulance account:**
- Create a `User` (e.g., username: `ambulance1`, password: `test1234`)
- Create a `UserProfile` with role = `ambulance`

**3. A Citizen account:**
- Go to **http://127.0.0.1:8000/citizen-signup/** to self-register
- After login, go to **Edit Profile** and fill in your Aadhaar number and health details

---

### Step 9 — Test the Emergency Flow

1. Log in as the **hospital** → Update ER rooms, ICU beds, and specialist availability
2. Log in as the **ambulance** → Update your GPS location → Select patient type → Click "Find Hospitals" → Confirm transport with the citizen's Aadhaar number
3. Log back in as the **hospital** → See the incoming patient with full medical details and ETA
4. Log in as the **citizen** → Send a distress signal → Log in as the ambulance to see the signal appear

---

### Common Issues

**`ModuleNotFoundError: No module named 'rest_framework'`**
Run: `pip install djangorestframework`

**`ModuleNotFoundError: No module named 'requests'`**
Run: `pip install requests`

**OpenRouteService returns an error**
The coordinates may be outside routable road networks (e.g., in the ocean). Use realistic coordinates for your region.
Also verify your API key quota at https://openrouteservice.org/plans/

**`Hospital matching query does not exist`**
The logged-in hospital user has no linked `Hospital` record in the database. Create one in the admin panel.

**Port already in use**
Run on a different port: `python manage.py runserver 8080`

---

## Security Notes for Production

The project is configured for local development only. Before deploying:

- Set `DEBUG = False` in `settings.py`
- Replace the `SECRET_KEY` with a strong random value
- Add your domain to `ALLOWED_HOSTS`
- Move the OpenRouteService API key to an environment variable
- Switch from SQLite to PostgreSQL or MySQL
- Configure a proper static file server (e.g., WhiteNoise or Nginx)
