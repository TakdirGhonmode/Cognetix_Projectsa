# Enterprise Workflow Automation System

## 1. Project Overview
The **Enterprise Workflow Automation System** is a production-grade Python 3.10+ enterprise system built with **FastAPI**, **SQLAlchemy**, and **Pydantic**. It automates structured business processes across departments (such as HR, Finance, Procurement, and Compliance). Features include configurable workflow template design, dynamic task routing (by User, Role, or Department), state-machine execution tracking, approval/rejection/modification loops, tamper-resistant SHA-256 audit logging, operational monitoring dashboards, and bottleneck analytics.

---

## 2. System Architecture
The application follows a clean modular architecture:

```text
enterprise-workflow-system/
│── models/                     # SQLAlchemy ORM Database Models
│   ├── user.py                 # User & RBAC models
│   ├── workflow.py             # WorkflowTemplate & WorkflowStage models
│   ├── instance.py             # WorkflowInstance & TaskInstance models
│   └── audit.py                # Tamper-resistant AuditLog model
│── schemas/                    # Pydantic Schemas for Request/Response validation
│── routes/                     # REST API Endpoint Controllers
│   ├── auth.py                 # Authentication endpoints (/auth/register, /auth/login)
│   ├── templates.py            # Workflow Templates CRUD (/templates)
│   ├── instances.py            # Workflow Execution (/instances)
│   ├── tasks.py                # Task Queue & Approvals (/tasks)
│   ├── analytics.py            # Operational Analytics (/analytics)
│   └── audit.py                # Audit Trail & Verification (/audit)
│── services/                   # Business Services Layer
│   ├── audit_service.py        # Cryptographic Hash Chaining & Verification
│   ├── analytics_service.py    # Bottlenecks, SLA & Throughput Calculations
│   └── notification_service.py # Real-time Event & Alert Dispatcher
│── notifications/              # Extensibility Hooks (Email & WebSocket stubs)
│── auth/                       # OAuth2, JWT Security & RBAC Dependencies
│── workflow_engine.py          # State-Machine & Dynamic Task Routing Engine
│── database.py                 # Database Engine (MySQL primary, SQLite workflow.db fallback)
│── workflow.db                 # SQLite development database (auto-created fallback)
│── main.py                     # FastAPI Application Entry Point
│── seed_data.py                # Database Initializer & Enterprise Demo Seeder
│── static/                     # Monitoring Web Dashboard SPA UI
├── tests/                      # Pytest Automated Test Suite
├── requirements.txt            # Project Dependencies
└── README.md                   # System Documentation
```

---

## 3. Database Schema
The database uses SQLAlchemy 2.0 supporting **MySQL** (`mysql+pymysql://root:Takdir%401234@localhost:3306/enterprise_workflow`) with automatic fallback to **SQLite** (`workflow.db`).

- **users**: `id`, `username`, `email`, `hashed_password`, `role`, `department`, `is_active`, `created_at`
- **workflow_templates**: `id`, `name`, `description`, `department`, `is_active`, `created_by_id`, `created_at`, `updated_at`
- **workflow_stages**: `id`, `template_id`, `stage_order`, `name`, `required_role`, `required_department`, `assigned_user_id`, `approval_required`, `sla_hours`
- **workflow_instances**: `id`, `template_id`, `title`, `initiator_id`, `current_stage_id`, `status`, `payload`, `created_at`, `updated_at`, `completed_at`
- **task_instances**: `id`, `instance_id`, `stage_id`, `assigned_role`, `assigned_department`, `assigned_user_id`, `status`, `decision_reason`, `created_at`, `completed_at`
- **audit_logs**: `id`, `instance_id`, `stage_id`, `actor_id`, `action`, `details`, `previous_hash`, `current_hash`, `timestamp`

---

## 4. Workflow Engine Design
The workflow engine (`workflow_engine.py`) operates as a dynamic state-machine. It decouples stage definitions from hardcoded application logic, storing workflow steps dynamically. Templates can be added or updated without resetting or corrupting running workflow instances.

---

## 5. State Transition Logic
All workflow instances and tasks obey strict state enumerations:

- `PENDING`: Awaiting user, role, or department action
- `APPROVED`: Action approved by assigned authority
- `REJECTED`: Request rejected and routed back to previous stage or terminated
- `MODIFICATION_REQUESTED`: Returned to initiator for data correction
- `COMPLETED`: Workflow successfully completed all configured stages

```text
                  [ PENDING ]
                     │
         ┌───────────┼───────────┐
         ▼           ▼           ▼
    [ APPROVED ] [ REJECTED ] [ MODIFICATION_REQUESTED ]
         │           │           │
         ▼           ▼           ▼
   [ NEXT_STAGE ] [ PREVIOUS ] [ CURRENT_STAGE ]
         │           │
         ▼           │
   [ COMPLETED ] ◄───┘
```

---

## 6. Task Routing Mechanism
Tasks are routed dynamically to assignees matching:
1. **Direct User ID**: Task assigned to a specific individual (`assigned_user_id`)
2. **Assigned Role**: Task assigned to any user holding the role (e.g. `Finance_Approver`, `HR_Approver`, `Procurement_Officer`)
3. **Assigned Department**: Task assigned to users in the target department (e.g. `Finance`, `HR`, `Procurement`, `Compliance`)

---

## 7. Approval and Rejection Logic
- **Approval (`POST /tasks/{id}/approve`)**: Marks task `APPROVED`. Advances `WorkflowInstance.current_stage_id` to stage N+1. If no further stages remain, instance transitions to `COMPLETED`.
- **Rejection (`POST /tasks/{id}/reject`)**: Mandatorily requires a rejection reason. Routes instance back to the previous stage (N-1). If rejected at Stage 1, workflow transitions to `REJECTED` and terminates.
- **Request Modification (`POST /tasks/{id}/modify`)**: Transitions status to `MODIFICATION_REQUESTED` and routes task back to the workflow initiator for corrections.

---

## 8. Audit Logging System
Every state change, routing action, and user decision generates a tamper-resistant entry in `audit_logs`.
Each audit log entry computes a cryptographic SHA-256 hash chain:

```
current_hash = SHA256(previous_hash | instance_id | stage_id | actor_id | action | timestamp | details)
```

Integrity can be validated at any time using `GET /audit/verify`.

---

## 9. Monitoring APIs
- `GET /analytics/approval-time`: Average approval duration per workflow template and per stage
- `GET /analytics/bottlenecks`: Stage-wise bottleneck analysis identifying queue buildup and SLA breaches
- `GET /analytics/completion-rate`: Overall throughput breakdown (Completed vs Rejected vs Active)

---

## 10. Authentication and RBAC
The system utilizes OAuth2 Password Bearer authentication with JWT access tokens (signed via HMAC-SHA256 using `pyjwt`) and password hashing via `bcrypt`.

**Available Roles:**
| Role                    | Access Level                                 |
|-------------------------|----------------------------------------------|
| `Admin`                 | Full system access, override all permissions |
| `Manager`               | Approve/reject department-level tasks         |
| `Employee`              | Submit workflow requests                     |
| `Finance_Approver`      | Finance department approvals                 |
| `HR_Approver`           | HR department approvals                      |
| `Procurement_Officer`   | Procurement fulfillment tasks                |
| `Compliance_Officer`    | Compliance review tasks                      |

---

## 11. Demo User Accounts

The following accounts are automatically seeded into the database on first startup:

| Username              | Password       | Role                  | Department   | What You Can Do                                              |
|-----------------------|----------------|-----------------------|--------------|--------------------------------------------------------------|
| `admin`               | `AdminPass123!`| Admin                 | Executive    | Full access — manage all workflows, users, templates, audit  |
| `john_employee`       | `Pass123!`     | Employee              | Operations   | Initiate new workflow requests                               |
| `hr_manager`          | `Pass123!`     | HR_Approver           | HR           | Approve/reject HR onboarding workflow tasks                  |
| `finance_approver`    | `Pass123!`     | Finance_Approver      | Finance      | Approve/reject finance & budget tasks                        |
| `procurement_lead`    | `Pass123!`     | Procurement_Officer   | Procurement  | Execute procurement purchase order tasks                     |
| `compliance_head`     | `Pass123!`     | Compliance_Officer    | Compliance   | Review compliance workflow tasks                             |

> **Note:** The `admin` account has override privileges across all roles and departments.

---

## 12. Installation
Ensure Python 3.10 or higher is installed:
```bash
python --version
```

Install dependencies:
```bash
pip install fastapi
pip install uvicorn
pip install sqlalchemy
pip install pydantic
pip install pymysql
pip install bcrypt
pip install pyjwt
pip install passlib
pip install pytest
pip install httpx
```

---

## 13. Environment Setup

**MySQL (Primary — Recommended):**
- MySQL Server running on `localhost:3306`
- Username: `root`
- Password: `Takdir@1234`
- The application **automatically creates** the `enterprise_workflow` database and all tables on first startup — no manual SQL needed.

**SQLite (Automatic Fallback):**
- If MySQL is unavailable, SQLite (`workflow.db`) is used automatically — zero configuration required.

**Optional Environment Variables:**
```
MYSQL_USER=root
MYSQL_PASSWORD=Takdir@1234
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB_NAME=enterprise_workflow
SECRET_KEY=enterprise-secret-key-workflow-automation-2026-super-safe
```

---

## 14. How to Run the System

```bash
# Step 1 — Install all dependencies
pip install fastapi uvicorn sqlalchemy pydantic pymysql bcrypt pyjwt passlib pytest httpx

# Step 2 — Start the application server
python -m uvicorn main:app --reload

# Step 3 — Open Interactive Swagger API documentation
# Visit: http://127.0.0.1:8000/docs

# Step 4 — Open the Enterprise Monitoring Web Dashboard
# Visit: http://127.0.0.1:8000/
```

---

## 15. Testing

### Method 1 — Run Automated Tests (Pytest)

```bash
python -m pytest -v
```

**Expected Output:**
```
tests/test_analytics.py::test_analytics_metrics         PASSED ✅
tests/test_audit.py::test_audit_log_hash_chaining       PASSED ✅
tests/test_auth.py::test_user_registration_and_login    PASSED ✅
tests/test_workflow_engine.py::test_workflow_lifecycle_approval  PASSED ✅
tests/test_workflow_engine.py::test_workflow_rejection_routing   PASSED ✅

5 passed
```

**Test Coverage:**
- `tests/test_auth.py` — User registration, JWT login, auth token validation
- `tests/test_workflow_engine.py` — Multi-stage approvals, rejection routing, modification requests
- `tests/test_audit.py` — SHA-256 hash chaining and tamper-resistance verification
- `tests/test_analytics.py` — Completion rate, bottleneck, and approval time metrics

---

### Method 2 — Test via Swagger UI (Step by Step)

**Step 1 — Start the server:**
```bash
python -m uvicorn main:app --reload
```

**Step 2 — Open:** `http://127.0.0.1:8000/docs`

**Step 3 — Login:**
- Find `POST /auth/login` → click **Try it out**
- Enter `username: admin` and `password: AdminPass123!`
- Click **Execute** → copy the `access_token`
- Click **Authorize 🔓** (top right) → paste `Bearer <token>` → Authorize

**Step 4 — Test Endpoints in Order:**

| # | Endpoint | Body / Params | Expected Result |
|---|---|---|---|
| 1 | `GET /templates` | — | Returns 2 pre-loaded workflow templates |
| 2 | `GET /instances/active` | — | Returns 2 active demo workflow instances |
| 3 | `POST /instances` | `{"template_id": 1, "title": "PO-TEST-001", "payload": {"amount": 8000}}` | New instance created with status `PENDING` |
| 4 | `GET /tasks/pending` | — | Returns pending tasks (note the task `id`) |
| 5 | `POST /tasks/{id}/approve` | `{"comments": "Approved!"}` | Workflow advances to next stage |
| 6 | `POST /tasks/{id}/reject` | `{"reason": "Budget exceeded"}` | Workflow routes back to previous stage |
| 7 | `POST /tasks/{id}/modify` | `{"comments": "Please revise amount"}` | Task returned to initiator |
| 8 | `GET /analytics/completion-rate` | — | Returns completion %, rejection %, totals |
| 9 | `GET /analytics/bottlenecks` | — | Returns stage-wise SLA breach analysis |
| 10 | `GET /analytics/approval-time` | — | Returns avg approval time per stage |
| 11 | `GET /audit` | — | Returns full audit log with SHA-256 hashes |
| 12 | `GET /audit/verify` | — | Returns `"is_valid": true` — chain intact ✅ |

---

### Method 3 — Test via Web Dashboard

**Open:** `http://127.0.0.1:8000/`

| Action | Steps |
|---|---|
| **Login** | Enter `admin` / `AdminPass123!` → Sign In |
| **View KPIs** | Dashboard tab — see total workflows, completion rate, bottlenecks |
| **Approve a Task** | ⚡ Pending Approvals → click **Approve** → enter comments → confirm |
| **Reject a Task** | ⚡ Pending Approvals → click **Reject** → enter reason → confirm |
| **Request Modification** | ⚡ Pending Approvals → click **Modify** → enter instructions |
| **Launch New Workflow** | Click `+ Launch New Workflow` → select template → enter title → Start |
| **View Stage Flow** | 🔄 Active Workflows → click `View Flow` → see visual stage diagram |
| **Check Audit Integrity** | 🛡️ Audit Trail tab → click **Verify Log Chain Integrity** → `VALID` ✅ |

---

### Method 4 — End-to-End Demo Flow

Complete this full workflow lifecycle test:

```
1. Login as:  john_employee / Pass123!
   Action:    Launch New Workflow → "Purchase Order Expense Approval"
              Title: "PO-2026-TEST: Laptop Purchase $6,000"

2. Login as:  finance_approver / Pass123!
   Action:    Go to Pending Approvals → Approve task
              Comment: "Budget approved for Q3"
              → Workflow advances to Stage 2

3. Login as:  procurement_lead / Pass123!
   Action:    Go to Pending Approvals → Approve final task
              Comment: "Purchase order raised and fulfilled"
              → Workflow status becomes COMPLETED ✅

4. Login as:  admin / AdminPass123!
   Action:    Go to Audit Trail → Click "Verify Log Chain Integrity"
              → Result: is_valid: true — All hashes intact ✅

5. Check Analytics:
   GET /analytics/completion-rate  → completion_rate_percent updated
   GET /analytics/approval-time    → avg_hours calculated per stage
```

---

## 16. Future Expansion
The system architecture includes extension hooks for future enterprise capabilities:
- **Notification Services (`services/notification_service.py`, `notifications/`)**: Modular providers for email and WebSocket real-time notifications upon task routing and SLA escalation.
- **SLA Breach Monitoring**: Automatic alerts when task wait times exceed configured `sla_hours` per stage.
- **Advanced BI Analytics**: Exportable CSV/PDF audit compliance and performance throughput reports.
- **Department-level Dashboards**: Per-department workflow visibility and approval metrics.
