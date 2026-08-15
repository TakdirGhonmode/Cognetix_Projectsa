# SaaS Backend Platform (Python Capstone Project)

A scalable, multi-tenant Python SaaS Backend Platform built with **FastAPI**, **SQLAlchemy**, **PyJWT**, **Bcrypt**, and **Pydantic v2**. 

Designed to support multi-user tenant architecture, role-based authorization (RBAC), subscription plan management, real-time quota tracking, system alert generation, usage analytics, billing webhooks, and modular expansion.

---

## Technical Stack

- **Programming Language**: Python 3.10+ (Tested on Python 3.14)
- **Web Framework**: FastAPI (Async-ready, OpenAPI/Swagger integrated)
- **Database & ORM**: SQLAlchemy 2.0 (SQLite default, PostgreSQL compatible)
- **Authentication**: PyJWT (Access & Refresh tokens), Bcrypt password hashing
- **Data Validation**: Pydantic v2 with `email-validator`
- **Testing**: Pytest with HTTPX and FastAPI TestClient

---

## Flowchart & Architecture

```
[Start] -> [Initialize FastAPI App] -> [Setup Database & Models]
            |
            v
       [User Registration (/register)] -> [Assign Subscription Plan (Free/Basic/Premium)]
            |
            v
       [Authenticate User (JWT /login)] -> [Apply Role-Based Authorization (RBAC)]
            |
            v
       [Generate System Alert] -> [Track Usage & Data (Daily Quotas)] -> [Persist Securely (ORM)] -> [End]
```

### Layered Architecture Structure
```
saas-backend-platform/
├── config.py                # Environment settings & tier matrix configuration
├── database.py              # SQLAlchemy engine, SessionLocal, Base & get_db dependency
├── main.py                  # FastAPI application entry point, middleware, routes, exception handlers
├── seed.py                  # Seeder script populating subscription plans, superadmin, sample org
├── requirements.txt         # Project dependencies
├── models/                  # SQLAlchemy ORM Data Models
│   ├── user.py              # User account model
│   ├── organization.py      # Organization (Tenant) & OrganizationMember (RBAC) models
│   ├── subscription.py      # SubscriptionPlan & TenantSubscription models
│   ├── alert.py             # System & Quota Alert model
│   ├── usage.py             # API Usage Log model
│   └── billing.py           # Invoice & Transaction model
├── schemas/                 # Pydantic Schemas for Request/Response Validation
│   ├── response_wrapper.py  # Standardized API response wrapper schemas
│   ├── auth.py              # Auth request & token schemas
│   ├── user.py              # User profile schemas
│   ├── organization.py      # Tenant & Member schemas
│   ├── subscription.py      # Subscription plan & assignment schemas
│   ├── alert.py             # Alert request & response schemas
│   ├── usage.py             # Usage stats & Analytics schemas
│   └── billing.py           # Invoice & Webhook schemas
├── auth/                    # Security & Authentication Core
│   ├── security.py          # Password hashing (bcrypt) & JWT issuance/validation
│   └── dependencies.py      # get_current_user, require_role, require_plan_feature
├── services/                # Business Logic Service Layer
│   ├── auth_service.py      # Register & Login business logic
│   ├── user_service.py      # User profile management logic
│   ├── org_service.py       # Organization multi-tenancy & membership logic
│   ├── subscription_service.py # Plan assignment & upgrade/downgrade validation
│   ├── alert_service.py     # System alert creation, retrieval, and quota enforcement
│   ├── usage_service.py     # Usage logging & quota enforcement logic
│   └── billing_service.py   # Invoice generation & payment webhook logic
├── routes/                  # FastAPI API Routers
│   ├── auth_routes.py       # Auth endpoints (/api/v1/auth)
│   ├── user_routes.py       # User endpoints (/api/v1/users)
│   ├── org_routes.py        # Organization endpoints (/api/v1/organizations)
│   ├── sub_routes.py        # Subscription endpoints (/api/v1/subscriptions)
│   ├── alert_routes.py      # Alert endpoints (/api/v1/alerts)
│   ├── usage_routes.py      # Usage & Analytics endpoints (/api/v1/usage, /analytics)
│   └── billing_routes.py    # Billing & Webhook endpoints (/api/v1/billing)
├── tests/                   # Automated Pytest Suite
│   ├── conftest.py          # Test database fixtures & test client setup
│   ├── test_auth.py         # Authentication tests
│   ├── test_org.py          # Tenant isolation & membership tests
│   ├── test_subscription.py # Subscription plan assignment & quota tests
│   ├── test_alerts.py       # Alert creation & plan-limit tests
│   └── test_rbac.py         # Role-based access control tests
└── README.md                # Complete project documentation
```

---

## Authentication & Security Flow

1. **User Registration**: `POST /api/v1/auth/register` creates a user record with password hashed using `bcrypt`.
2. **User Login**: `POST /api/v1/auth/login` verifies password and issues two tokens:
   - **Access Token**: Short-lived JWT (24 hours) signed with `HS256`.
   - **Refresh Token**: Long-lived JWT (7 days) used to request new access tokens via `POST /api/v1/auth/refresh`.
3. **Protected Requests**: Clients attach `Authorization: Bearer <access_token>` header on protected endpoints.
4. **Dependency Injection**: `get_current_user` extracts, decodes, and validates token claims on incoming requests.

---

## Role-Based Access Control (RBAC)

RBAC permissions are scoped per tenant organization using the `X-Organization-ID` header:

| Role | Description | Permissions |
| :--- | :--- | :--- |
| **`SUPERADMIN`** | System Superadmin | Full global system access across all tenants and users. |
| **`ADMIN`** | Organization Admin | Manage tenant settings, assign subscription plans, add/remove members, issue/delete alerts. |
| **`ORG_OWNER`** | Organization Owner | Same privileges as ADMIN plus ownership control. Created automatically on org creation. |
| **`MANAGER`** | Manager | Can add organization members and generate/manage system alerts. Cannot change subscription plans. |
| **`USER`** | Member | View tenant details, view usage metrics, view alerts. Cannot modify membership or plans. |

---

## Subscription Matrix & Limits

| Plan | Alert Quota | Daily API Quota | Max Members | Analytics Dashboard | Data Export (CSV) | Price / Month |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Free** | **10 alerts** | **100 calls/day** | 3 members | Locked | Locked | \$0.00 |
| **Basic** | **100 alerts** | **1,000 calls/day** | 10 members | Included | Locked | \$29.99 |
| **Premium** | **Unlimited** | **Unlimited** (100k/day)| 100 members | Included | Included | \$99.99 |

### Quota & Quota Alert Logic
- **Alert Quota Enforcement**: `AlertService.create_alert()` verifies total tenant alerts against plan `max_alerts`.
- **API Quota Tracking**: `UsageService.log_request()` tracks 24-hour API request volume. Automatically issues 80% warning and 100% capacity alerts.
- **Downgrade Safety**: Plan downgrades (`POST /api/v1/subscriptions/assign`) check active member count against target plan limits before permitting plan changes.

---

## Structured API Response Format

All responses follow a uniform JSON envelope:

### Success Example
```json
{
    "success": true,
    "message": "Operation completed successfully",
    "data": {
        "id": 1,
        "email": "user@example.com"
    }
}
```

### Error Example
```json
{
    "success": false,
    "message": "Access denied: Not a member of this organization",
    "errors": [
        "User is not associated with specified tenant ID."
    ]
}
```

---

## API Endpoints Summary

### Authentication
- `POST /api/v1/auth/register` (User Signup)
- `POST /api/v1/auth/login` (User Login -> JWT Tokens)
- `POST /api/v1/auth/refresh` (Refresh Access Token)
- `GET /api/v1/auth/me` (Current Profile)

### User Management
- `GET /api/v1/users` (Superadmin List Users)
- `GET /api/v1/users/{id}` (Get User Details)
- `PUT /api/v1/users/me` (Update Profile)

### Organizations & Tenants
- `POST /api/v1/organizations` (Create Tenant Org)
- `GET /api/v1/organizations` (List User's Orgs)
- `POST /api/v1/organizations/{id}/members` (Add Member - RBAC & Subscription Check)
- `GET /api/v1/organizations/{id}/members` (List Org Members)
- `DELETE /api/v1/organizations/{id}/members/{user_id}` (Remove Member)

### Subscriptions
- `GET /api/v1/subscriptions` (List Available Plans)
- `GET /api/v1/subscriptions/current` (Get Tenant Subscription)
- `POST /api/v1/subscriptions/assign` (Upgrade/Downgrade Plan)
- `POST /api/v1/subscriptions/cancel` (Cancel Subscription)

### System Alerts
- `POST /api/v1/alerts` (Create System Alert - Plan Limit Checked)
- `GET /api/v1/alerts` (List Organization Alerts)
- `DELETE /api/v1/alerts/{id}` (Dismiss/Delete Alert)

### Usage Tracking & Analytics
- `GET /api/v1/usage` (Usage Stats & Quota Alerts)
- `GET /api/v1/analytics/dashboard` (Analytics - Plan Gated)
- `GET /api/v1/analytics/export` (CSV Export - Premium Plan Gated)

### Billing & Payments
- `GET /api/v1/billing/invoices` (Get Invoice History)
- `POST /api/v1/billing/webhook` (Stripe Payment Webhook Handler)

---

## Environment Setup & Execution

### 1. Clone & Setup Virtual Environment
```bash
git clone <repository_url>
cd SaaSBackendPlatform

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Variables Configuration (`.env`)
Create a `.env` file in the root directory:
```env
APP_NAME="SaaS Backend Platform"
ENVIRONMENT="development"
SECRET_KEY="super-secret-jwt-key-for-saas-platform-change-in-production-32bytes"
DATABASE_URL="sqlite:///./saas.db"
```

### 3. Seed Database
Run the seeder script to populate default plans (`Free`, `Basic`, `Premium`), superadmin user (`admin@saas.com`), and sample organization (`Acme Corp`):
```bash
python seed.py
```

### 4. Run Backend Server
```bash
uvicorn main:app --reload
```
The server will start at `http://127.0.0.1:8000`.

---

## Interactive API Documentation

- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## Automated Testing

Execute the complete automated `pytest` test suite:
```bash
pytest
```

---

## Testing with Postman

1. **Register User**: `POST http://127.0.0.1:8000/api/v1/auth/register` with body `{"email": "user@example.com", "password": "Password123!", "full_name": "User"}`.
2. **Login & Get JWT**: `POST http://127.0.0.1:8000/api/v1/auth/login`. Copy `access_token` from response `data`.
3. **Set Authorization Header**: In Postman, add header `Authorization: Bearer <access_token>`.
4. **Create Organization**: `POST http://127.0.0.1:8000/api/v1/organizations` with body `{"name": "My Org", "slug": "my-org"}`. Copy `id` from response (e.g., `1`).
5. **Set Tenant Context**: Add header `X-Organization-ID: 1`.
6. **Generate Alert**: `POST http://127.0.0.1:8000/api/v1/alerts` with body `{"title": "Warning", "message": "High usage", "severity": "WARNING"}`.
7. **Check Quota & Usage**: `GET http://127.0.0.1:8000/api/v1/usage`.
