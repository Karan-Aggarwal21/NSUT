# MindPlay: AI-Based Cognitive Gaming and Memory Assistance Platform

MindPlay is an accessible, web-based cognitive activity module designed for elderly users, particularly individuals who may experience memory or cognitive difficulties associated with ageing, dementia, or Alzheimer's disease.

> **Important Clinical & Ethical Disclaimer:**  
> These activities are experimental cognitive games designed for gentle mental stimulation, observation, and engagement. They are **not validated clinical diagnostic instruments**. Do **not** label their scores as dementia scores or use them to diagnose Alzheimer's disease or any clinical condition.

---

## 1. System Architecture

```text
                    NEXT.JS FRONTEND (Port 3000)
                           |
          +----------------+----------------+
          |                |                |
     Activity 1       Activity 2        Activity 3
     Object Memory    Circle Search    Calculation & Recall
          |                |                |
          +----------------+----------------+
                           |
                      Activity 4
                    Shape Recognition
                           |
                           v  REST APIs (JSON)
                   FASTAPI BACKEND (Port 8000)
                           |
          +----------------+----------------+
          |                |                |
     Task Generator    Scoring Engine    Session Manager
          |                |                |
          +----------------+----------------+
                           |
                           v
              PostgreSQL / SQLite Database
                           |
                           v
                 Results & Progress API
                           |
                           v
                    NEXT.JS DASHBOARD
```

---

## 2. The Four Cognitive Activities

1. **Activity 1: Object Sequence Memory**
   - Immediate visual sequence recall using familiar objects (Apple, Book, Key, Cup, Ball, Spoon, Clock, Shoe, Flower, Comb).
   - Displayed one by one with customizable duration (accessible viewing extension available).
   - Reconstructed using high-contrast, labeled sequence slots.
   - Authoritative backend scoring: position-wise accuracy, total objects, exact sequence boolean.

2. **Activity 2: Circle Identification and Attention**
   - Visual attention task using clear geometric shapes (circles, squares, triangles, rectangles).
   - Randomly generated grid (3×3 for Easy, 4×4 for Medium, 5×5 for Advanced).
   - Authoritative backend scoring: target detection rate (`correct_circles / total_circles`) and false-selection rate (`incorrect_non_circles / total_non_circles`).

3. **Activity 3: Basic Calculation and Delayed Word Recall**
   - **Part B (Word Presentation)**: 3 target familiar words displayed first for 3 seconds each.
   - **Part A (Intervening Calculation)**: 6 simple arithmetic questions (e.g., 2 + 1 = ?) presented one per screen to create a natural 30–60s delay.
   - **Part B (Delayed Word Recognition)**: 6 candidate cards presented to test delayed recognition.
   - Separate, uncombined scores reported for arithmetic accuracy and delayed word recognition.

4. **Activity 4: Shape Recognition and Spatial Reasoning**
   - Mode A: Single target shape matching.
   - Mode B: Sequence pattern row matching.
   - Authoritative backend scoring for visual pattern discrimination.

---

## 3. Technology Stack

- **Frontend**: Next.js 16 (App Router), TypeScript, Tailwind CSS, Lucide React, Recharts.
- **Backend**: Python 3.10+, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic.
- **Database**: PostgreSQL (production/staging) or SQLite (zero-config local dev), using JSONB / JSON storage for task metadata and authoritative scores.

---

## 4. Quick Start & Setup Instructions

### Prerequisites
- Node.js (v18+)
- Python (v3.10+)

### Backend Setup

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment:**
   ```bash
   cp .env.example .env
   ```
   *By default, `DATABASE_URL` is configured to `sqlite:///./cognitive_platform.db` for instant zero-dependency execution. For PostgreSQL, set:*
   ```env
   DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/cognitive_platform
   ```

5. **Apply Database Migrations:**
   ```bash
   alembic upgrade head
   ```

6. **Start the FastAPI backend server:**
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
   - API Docs will be available at: [http://127.0.0.1:8000/api/v1/docs](http://127.0.0.1:8000/api/v1/docs)

---

### Frontend Setup

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Build the production bundle:**
   ```bash
   npm run build
   ```

4. **Start the Next.js development server:**
   ```bash
   npm run dev
   ```
   - Open your browser at: [http://localhost:3000](http://localhost:3000)

---

## 5. Automated Tests

Run backend unit and integration tests covering all 4 activities, edge-case validations, duplicate submission prevention, and scoring accuracy:

```bash
cd backend
venv/bin/pytest -v
```

All 13 test suites execute and validate:
- Exact and partial sequence matches for Object Memory.
- Rejection of invalid object IDs and duplicate selections.
- Circle detection and false-selection rate mathematics.
- Prevention of score inflation through duplicate clicks.
- Intervening calculation accuracy and delayed word recognition metrics.
- Complete end-to-end multi-activity session lifecycle and longitudinal progress tracking.

---

## 6. Main Application Routes

- `/`: Calm landing page with high contrast and accessibility focus.
- `/assessment`: Session introduction, optional age group, and difficulty selection.
- `/assessment/object-memory`: Activity 1 (Object Sequence Memory).
- `/assessment/circle-search`: Activity 2 (Circle Identification & Attention).
- `/assessment/calculation-recall`: Activity 3 (Calculation & Delayed Word Recall).
- `/assessment/shape-recognition`: Activity 4 (Shape Recognition & Spatial Reasoning).
- `/assessment/complete`: Session completion summary with one card per activity and non-clinical notices.
- `/progress`: User longitudinal session history with interactive trend charts (Recharts).
- `/admin`: Development diagnostics and aggregate database metrics (no patient PII).
