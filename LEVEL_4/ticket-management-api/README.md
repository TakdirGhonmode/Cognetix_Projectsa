# Customer Support Ticket Management API

A robust RESTful API built with **FastAPI**, **SQLAlchemy**, and **MySQL** for managing customer support tickets with JWT Authentication, Role-Based Access Control (RBAC), Status Lifecycle Validation, Audit Logging, and filtering.

---

## 🛠️ Technology Stack

- **Framework**: FastAPI
- **Database**: MySQL with PyMySQL driver
- **ORM**: SQLAlchemy
- **Authentication**: JWT (`python-jose`) with Bearer token authentication
- **Password Hashing**: `passlib` with `bcrypt`
- **Configuration**: `python-dotenv` (.env file support)

---

## 📂 Project Structure

```text
ticket-management-api/
├── models.py      # SQLAlchemy database models (User, Ticket, TicketHistory)
├── schemas.py     # Pydantic request and response schemas
├── routes.py      # Ticket API endpoints with RBAC & Lifecycle logic
├── auth.py        # Authentication endpoints (Register, Login) & JWT dependencies
├── database.py    # Database connection & Session initialization
├── main.py        # FastAPI application entrypoint
├── README.md      # Project documentation
└── .env           # Environment variables (Database URL, JWT Secret)
```

---

## ⚙️ Configuration & Setup

### 1. Prerequisites
- Python 3.9+
- MySQL Server running locally on port 3306

### 2. Environment Variables (`.env`)
Create or edit `.env` in the project root:
```env
DATABASE_URL=mysql+pymysql://root:Takdir%401234@localhost:3306/ticket_management
SECRET_KEY=ticket-management-secret-key-super-secure-jwt
ALGORITHM=HS256
```

### 3. Run the Server
Execute the following command in the project directory:
```bash
python -m uvicorn main:app --reload
```

Interactive Swagger documentation will be available at:
👉 **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

---

## 🔐 Roles & Permissions (RBAC)

| Action | User Role | Admin Role |
| :--- | :---: | :---: |
| Register / Login | ✅ | ✅ |
| Create Ticket | ✅ | ✅ |
| View Own Tickets | ✅ | ✅ |
| View All Tickets | ❌ | ✅ |
| Update Ticket (Description, Priority, Status, Assignee) | ❌ (`403 Forbidden`) | ✅ |
| Change Status (Close / Reopen) | ❌ (`403 Forbidden`) | ✅ |
| View Ticket Audit History | Own Tickets Only | All Tickets |

---

## 🔄 Ticket Status Lifecycle

Tickets follow a strict status transition workflow. Invalid status transitions return an `HTTP 400 Bad Request`.

```text
[Open] ──> [In Progress] ──> [Resolved] ──> [Closed] ──> [Reopened] ──> [In Progress]
```

- **Open**: Initial state when ticket is created.
- **In Progress**: Admin works on ticket.
- **Resolved**: Admin resolves the issue.
- **Closed**: Admin closes the ticket.
- **Reopened**: Admin reopens a closed ticket (transitions back to In Progress).

---

## 🏷️ Priority Levels

- `Low`
- `Medium`
- `High`
- `Critical`

---

## 📡 API Endpoints Summary

### Authentication (`/auth`)
- **`POST /auth/register`**: Register a new user or admin (`{"name": "...", "email": "...", "password": "...", "role": "User"|"Admin"}`)
- **`POST /auth/login`**: Authenticate and retrieve JWT Bearer access token

### Ticket Management (`/tickets`) - *Requires Bearer Token*
- **`POST /tickets/`**: Create a ticket (`{"customer_name": "...", "issue_description": "...", "category": "...", "priority": "Low"}`)
- **`GET /tickets/`**: Retrieve tickets (Users see own tickets; Admins see all). Query filters:
  - `status`: `Open`, `In Progress`, `Resolved`, `Closed`, `Reopened`
  - `priority`: `Low`, `Medium`, `High`, `Critical`
  - `date`: `YYYY-MM-DD` (created date)
- **`GET /tickets/{id}`**: Retrieve specific ticket details
- **`PUT /tickets/{id}`**: Update ticket priority, description, status, or assignee (*Admin Only*)
- **`GET /tickets/{id}/history`**: Retrieve timestamped audit log of all changes for a ticket
