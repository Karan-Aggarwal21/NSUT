# Cognivia Backend

**AI-Based Cognitive Gaming and Memory Assistance Platform for Elderly People**

Designed to support elderly individuals, including those living with dementia or Alzheimer's disease, with particular focus on accessibility and offline resilience for users in the North Eastern Region (NER) of India.

---

## 1. Architecture & Technology Stack

* **Language**: Python 3.12+
* **Framework**: FastAPI (modular routers and services architecture)
* **Database**: PostgreSQL 16
* **ORM**: SQLAlchemy 2.0 (Declarative Base with modern type annotations)
* **Migrations**: Alembic
* **Validation**: Pydantic v2 & `pydantic-settings`
* **Security & Auth**: OAuth2 Password Flow + JWT (HS256) access tokens & rotating refresh tokens
* **Password Hashing**: Argon2id via `passlib`
* **Containerisation**: Docker & Docker Compose
* **Testing**: Pytest & FastAPI `TestClient`

---

## 2. Project Structure

```
backend/
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
├── README.md
├── app/
│   ├── __init__.py
│   ├── main.py                    # Lifespan, CORS, health check, exception handlers
│   ├── config.py                  # Pydantic Settings configuration
│   ├── database.py                # Engine, SessionLocal, Base, get_db
│   ├── api/
│   │   ├── dependencies.py        # Auth & db session dependencies
│   │   └── v1/
│   │       ├── router.py          # Unified v1 router
│   │       └── endpoints/
│   │           ├── auth.py        # /auth/register, /auth/login, /auth/refresh, /auth/logout
│   │           ├── users.py       # /users/me (GET, PATCH, DELETE)
│   │           ├── profiles.py    # /profiles/me (GET, PATCH)
│   │           ├── cognitive.py   # /cognitive/sessions, /cognitive/results, /cognitive/history
│   │           ├── personalized.py# /personalized/items, /personalized/sessions, /personalized/results
│   │           ├── questionnaires.py # /questionnaires, /questionnaires/{id}/responses, /questionnaires/responses
│   │           ├── history.py     # /history, /history/summary
│   │           ├── sync.py        # /sync, /sync/status
│   │           ├── settings.py    # /settings/preferences
│   │           └── admin.py       # /admin/metrics, /admin/audit-logs, /admin/users/{id}/status
│   ├── models/
│   │   ├── user.py                # User, RefreshToken, UserRole
│   │   ├── user_profile.py        # UserProfile
│   │   ├── assessment_session.py  # AssessmentSession, SessionStatus
│   │   ├── activity_result.py     # ActivityResult
│   │   ├── personalized_item.py   # PersonalizedItem, ItemCategory
│   │   ├── questionnaire.py       # Questionnaire
│   │   ├── questionnaire_version.py # QuestionnaireVersion
│   │   ├── questionnaire_question.py# QuestionnaireQuestion, QuestionnaireOption
│   │   ├── questionnaire_response.py# QuestionnaireResponse
│   │   ├── questionnaire_answer.py  # QuestionnaireAnswer
│   │   └── audit_log.py           # AuditLog
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── profile.py
│   │   ├── cognitive.py
│   │   ├── personalized.py
│   │   ├── questionnaire.py
│   │   ├── history.py
│   │   ├── sync.py
│   │   └── settings.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── session_service.py
│   │   ├── result_service.py
│   │   ├── personalized_service.py
│   │   ├── questionnaire_service.py
│   │   ├── history_service.py
│   │   ├── sync_service.py
│   │   └── admin_service.py
│   ├── security/
│   │   ├── password.py            # Argon2id implementation
│   │   ├── tokens.py              # JWT encoding/decoding & SHA-256 token hashing
│   │   └── permissions.py         # Role and ownership authorization helpers
│   └── utils/
│       ├── exceptions.py          # HTTP exception subclasses
│       └── responses.py           # Standard envelope formatting
├── migrations/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 001_initial_schema.py
└── tests/
    ├── conftest.py
    ├── test_auth.py
    ├── test_users.py
    ├── test_cognitive.py
    ├── test_personalized.py
    ├── test_questionnaires.py
    ├── test_history.py
    └── test_sync.py
```

---

## 3. Quickstart Guide (No Docker Required)

You do **not** need Docker to run Cognivia. The backend is configured to run out-of-the-box on your local machine using SQLite (or a local PostgreSQL instance if you prefer).

### 3.1. Prerequisites
* Python 3.12+ (or Python 3.13)
* `pip`

### 3.2. Setup Virtual Environment & Dependencies
```bash
cd backend
python -m venv venv

# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 3.3. Environment Configuration
Copy `.env.example` to `.env` (it is already pre-configured to use local SQLite with no Docker):
```bash
cp .env.example .env
```

### 3.4. Start the Backend Server (Zero Docker)
Run the FastAPI development server:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
On startup, the application automatically:
1. Creates the local database schema (`cognivia.db`).
2. Seeds the default 7-question elderly memory and well-being check-in questionnaire.
3. Exposes the interactive API docs at [http://localhost:8000/docs](http://localhost:8000/docs).

### 3.5. Running Automated Tests
```bash
pytest -v
```
All 35 automated unit and integration tests run isolated in memory.

---

## 3.6. Optional: Using PostgreSQL / Docker (Optional)
If you wish to use PostgreSQL or Docker later:
1. In `.env`, uncomment `DATABASE_URL=postgresql+psycopg://cognivia_user:cognivia_pass@localhost:5432/cognivia_db`
2. Run database migrations: `alembic upgrade head`
3. Optional Docker Compose: `docker compose up -d`

---

## 4. REST API Overview & Example Payloads

### 4.1. Authentication
* `POST /api/v1/auth/register`
* `POST /api/v1/auth/login` (Form-based OAuth2) or `POST /api/v1/auth/login/json`
* `POST /api/v1/auth/refresh`
* `POST /api/v1/auth/logout`

**Register Request**:
```json
{
  "username": "elderly_user_1",
  "password": "SecurePassword123!",
  "email": "user@example.com"
}
```

### 4.2. Cognitive Activity Sessions & Game Endpoints
* `POST /api/v1/cognitive/sessions` (Create/register session, idempotent by `client_session_id`)
* `GET /api/v1/cognitive/sessions/{session_id}`
* `POST /api/v1/cognitive/sessions/{session_id}/complete`
* `GET /api/v1/cognitive/sessions/{session_id}/report` (Final assessment report for UI)

#### Game 1: Object Sequence Memory
* `POST /api/v1/cognitive/games/sequence/start`
  Generates sequence of everyday objects (e.g., `["apple", "book", "key"]`) with answer key hidden on the backend.
* `POST /api/v1/cognitive/games/sequence/submit`
  Evaluates user's recalled sequence.
  **Response**:
  ```json
  {
    "task_id": "seq-task-abc123",
    "total_positions": 3,
    "correct_positions": 3,
    "items_recalled": 3,
    "position_accuracy": 1.0,
    "recall_accuracy": 1.0,
    "exact_sequence_match": true,
    "score": 100.0,
    "response_time_seconds": 3.5,
    "attempts": 1
  }
  ```

#### Game 2: Circle Identification & Attention
* `POST /api/v1/cognitive/games/attention/start`
  Generates visual cancellation grid with hidden circle target IDs.
* `POST /api/v1/cognitive/games/attention/submit`
  Calculates signal detection metrics (True Positives, Misses, False Alarms).
  **Response**:
  ```json
  {
    "task_id": "att-task-xyz789",
    "total_targets": 5,
    "total_distractors": 11,
    "correct_selections": 5,
    "missed_targets": 0,
    "distractor_selections": 1,
    "precision": 0.8333,
    "recall": 1.0,
    "f1_score": 0.9091,
    "attention_score": 90.9,
    "response_time_seconds": 7.8
  }
  ```

#### Game 3: Personalized Memory Recognition
* `POST /api/v1/cognitive/games/personalized/start`
* `POST /api/v1/cognitive/games/personalized/submit`

#### Game 4: Visual Pattern Matching
* `POST /api/v1/cognitive/games/pattern/submit`

#### Final Assessment Session Report for UI Display
* `GET /api/v1/cognitive/sessions/{session_id}/report`
  Aggregates all game results in the session, groups domain scores (*Working Memory*, *Selective Attention*, *Personalized Recall*, *Processing Speed*), and integrates self-reported well-being questionnaire check-in.
  **Response**:
  ```json
  {
    "session_id": "uuid-here",
    "overall_score": 95.5,
    "performance_rating": "Excellent Engagement & Sharp Focus",
    "domains": [
      {
        "domain": "Working Memory",
        "score": 100.0,
        "performance_level": "High Engagement & Strong Accuracy",
        "tasks_completed": 1
      },
      {
        "domain": "Selective Attention",
        "score": 90.9,
        "performance_level": "High Engagement & Strong Accuracy",
        "tasks_completed": 1
      }
    ],
    "game_results": [...],
    "questionnaire_summary": {
      "completed": true,
      "emotional_wellbeing": "good",
      "level_of_concern": "not_concerned"
    },
    "clinical_disclaimer": "Cognivia is an engagement and cognitive assistance platform..."
  }
  ```

### 4.3. Personalised Memory Activities
* `POST /api/v1/personalized/items`
* `GET /api/v1/personalized/items`
* `PATCH /api/v1/personalized/items/{item_id}`
* `DELETE /api/v1/personalized/items/{item_id}`
* `POST /api/v1/personalized/sessions`

**Create Personalised Item Payload**:
```json
{
  "category": "familiar_person",
  "display_name": "Daughter Priya",
  "description": "Lives in Guwahati, visits on weekends",
  "image_reference": "local_storage://images/priya.jpg"
}
```

### 4.4. Questionnaire & Self-Reported Well-Being
* `GET /api/v1/questionnaires`
* `GET /api/v1/questionnaires/{slug_or_id}`
* `POST /api/v1/questionnaires/{slug_or_id}/responses`
* `GET /api/v1/questionnaires/responses/{response_id}`

**Submit Questionnaire Answers**:
```json
{
  "client_submission_id": "quest-sub-uuid-001",
  "questionnaire_version": "1.0",
  "completed_at": "2026-10-17T08:40:00Z",
  "answers": [
    {
      "question_id": "recent_memory_difficulties",
      "answer": "sometimes"
    },
    {
      "question_id": "difficulty_concentrating",
      "answer": "never"
    },
    {
      "question_id": "level_of_concern",
      "answer": "prefer_not_to_answer"
    }
  ]
}
```

### 4.5. Unified Activity History
* `GET /api/v1/history?start_date=2026-10-01T00:00:00Z&activity_category=cognitive`
* `GET /api/v1/history/summary`

Aggregates cognitive activities, personalised activities, and questionnaires into a clean chronological stream without leaking raw answers or conflating distinct categories.

### 4.6. Offline Synchronisation
* `POST /api/v1/sync`
* `GET /api/v1/sync/status`

Allows the Flutter app to batch upload pending SQLite records upon reconnection. Idempotent per-item processing guarantees that duplicate retries succeed safely and invalid items do not discard valid records in the batch.

---

## 5. Security, Ethics & Clinical Boundaries

1. **Non-Diagnostic Nature**: The platform strictly tracks engagement, memory recall, and subjective well-being. It explicitly **does not** generate medical diagnoses or dementia risk scores.
2. **Password Security**: Argon2id password hashing is enforced with cryptographic salts.
3. **Data Protection**: Personal photos are never stored as binary BLOBs in PostgreSQL; only verified local or remote image URIs are referenced.
4. **Strict Isolation**: Cross-user data access is strictly forbidden with resource ownership verification.
5. **Audit Trail**: Administrative actions (e.g., account deactivation) are recorded in an audit table without logging sensitive payloads or passwords.
