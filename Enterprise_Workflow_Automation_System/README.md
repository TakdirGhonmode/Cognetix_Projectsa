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
│── database.py                 # Database Engine (MySQL with SQLite workflow.db fallback)
│── workflow.db                 # SQLite development database
│── main.py                     # FastAPI Application Entry Point
│── seed_data.py                # Database Initializer & Enterprise Demo Seeder
│── static/                     # Monitoring Web Dashboard SPA UI
├── tests/                      # Pytest Automated Test Suite
├── requirements.txt            # Project Dependencies
└── README.md                   # System Documentation
```

---

## 3. Database Schema
The database uses SQLAlchemy 2.0 supporting MySQL (`mysql+pymysql://root:Takdir%401234@localhost:3306/enterprise_workflow`) with automatic fallback to SQLite (`workflow.db`).

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
- **Approval (`POST /tasks/{id}/approve`)**: Marks task `APPROVED`. Advances `WorkflowInstance.current_stage_id` to stage $N+1$. If no further stages remain, instance transitions to `COMPLETED`.
- **Rejection (`POST /tasks/{id}/reject`)**: Mandatorily requires a rejection reason. Routes instance back to the previous stage ($N-1$). If rejected at Stage 1, workflow transitions to `REJECTED` and terminates.
- **Request Modification (`POST /tasks/{id}/modify`)**: Transitions status to `MODIFICATION_REQUESTED` and routes task back to the workflow initiator for corrections.

---

## 8. Audit Logging System
Every state change, routing action, and user decision generates a tamper-resistant entry in `audit_logs`.
Each audit log entry computes a cryptographic SHA-256 hash:

$$\text{current\_hash} = \text{SHA256}(\text{previous\_hash} \mid \text{instance\_id} \mid \text{stage\_id} \mid \text{actor\_id} \mid \text{action} \mid \text{timestamp} \mid \text{details})$$

Integrity can be validated at any time using `GET /audit/verify` to verify that no log entry has been altered or deleted directly in the database.

---

## 9. Monitoring APIs
- `GET /analytics/approval-time`: Average approval duration per workflow template and per stage
- `GET /analytics/bottlenecks`: Stage-wise bottleneck analysis identifying queue buildup and SLA breaches
- `GET /analytics/completion-rate`: Overall throughput breakdown (Completed vs Rejected vs Active)

---

## 10. Authentication and RBAC
The system utilizes OAuth2 Password Bearer authentication with JWT access tokens signed via HMAC-SHA256 (`pyjwt`) and password hashing via `bcrypt`. Role-Based Access Control (RBAC) dependencies enforce permissions per endpoint:
- Roles: `Admin`, `Manager`, `Employee`, `Finance_Approver`, `HR_Approver`, `Procurement_Officer`, `Compliance_Officer`

---

## 11. API Documentation
FastAPI automatically generates interactive OpenAPI Swagger documentation at `http://127.0.0.1:8000/docs` and ReDoc at `http://127.0.0.1:8000/redoc`.

Endpoints include:
- **Auth**: `POST /auth/register`, `POST /auth/login`, `GET /auth/me`
- **Templates**: `POST /templates`, `GET /templates`, `GET /templates/{id}`, `PUT /templates/{id}`, `DELETE /templates/{id}`
- **Instances**: `POST /instances`, `GET /instances`, `GET /instances/active`, `GET /instances/completed`, `GET /instances/{id}`
- **Tasks**: `GET /tasks`, `GET /tasks/pending`, `POST /tasks/{id}/approve`, `POST /tasks/{id}/reject`, `POST /tasks/{id}/modify`
- **Analytics**: `GET /analytics/approval-time`, `GET /analytics/bottlenecks`, `GET /analytics/completion-rate`
- **Audit**: `GET /audit`, `GET /audit/verify`

---

## 12. Installation
Ensure Python 3.10 or higher is installed:
```bash
python --version
```

Install dependencies:
```bash
pip install fastapi uvicorn sqlalchemy pydantic pymysql bcrypt pyjwt passlib pytest httpx
```

---

## 13. Environment Setup
Create optional environment variables or rely on automatic defaults:
- `MYSQL_DATABASE_URL`: `mysql+pymysql://root:Takdir%401234@localhost:3306/enterprise_workflow`
- `SQLITE_DATABASE_URL`: `sqlite:///./workflow.db`
- `SECRET_KEY`: `enterprise-secret-key-workflow-automation-2026-super-safe`

---

## 14. How to Run the System

```bash
# 1. Install dependencies
pip install fastapi
pip install uvicorn
pip install sqlalchemy
pip install pydantic
pip install pymysql
pip install bcrypt
pip install pyjwt

# 2. Start the application server
uvicorn main:app --reload

# 3. Open Interactive Swagger API documentation
http://127.0.0.1:8000/docs

# 4. Open the Enterprise Monitoring Web Dashboard
http://127.0.0.1:8000/
```

---

## 15. Testing
Execute the automated test suite with `pytest`:

```bash
pytest
```

---

## 16. Future Expansion
The system architecture includes extension hooks for future enterprise capabilities:
- **Notification Services (`services/notification_service.py`, `notifications/`)**: Modular providers for email and WebSocket notifications upon task routing and SLA escalation.
- **SLA Breach Monitoring**: Real-time alerts when task wait times exceed `sla_hours`.
- **Advanced BI Analytics**: Exportable CSV/PDF audit and performance compliance reports.
