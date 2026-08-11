# Product Management REST API (Level 4 Project)

A Python-based RESTful API developed with **FastAPI**, **SQLAlchemy**, **SQLite**, **Pydantic**, and **JWT Authentication**. This backend service manages inventory data through secure HTTP endpoints with data validation, role-based access control, structured JSON error handling, and transaction logging.

---

## 🌟 Features

- **CRUD Operations**: Full support for Creating, Reading, Updating, and Deleting products.
- **Data Validation**: Strict Pydantic input validation (strictly positive prices `> 0`, non-negative quantities `>= 0`, unique product IDs, non-empty fields).
- **Authentication & Security**: JWT (JSON Web Token) Bearer authentication for user login/registration and secure endpoints.
- **Role-Based Access Control (RBAC)**: Restricts product deletion (`DELETE /products/{product_id}`) to users with an `admin` role.
- **Data Persistence**: Uses SQLite database (`products.db`) managed via SQLAlchemy ORM.
- **Transaction History**: Automatically records all create, update, and delete actions into a `transaction_history` table.
- **Standardized API Responses**: Every endpoint returns a uniform JSON envelope structure (`status`, `message`, `data`/`details`).
- **Interactive Documentation**: Built-in Swagger UI (`/docs`) and ReDoc (`/redoc`).
- **Automated Test Suite**: Pytest test suite covering endpoints, authentication, validation errors, and authorization logic.

---

## 📁 Project Structure

```
product-management-api/
│── main.py              # FastAPI app initialization, exception handlers, and router inclusion
│── config.py            # JWT and Database configuration settings
│── database.py          # SQLAlchemy SQLite database setup and session generator
│── models.py            # SQLAlchemy database models (Product, User, TransactionHistory)
│── schemas.py           # Pydantic schemas for request validation & API response envelopes
│── auth.py              # JWT token generation/validation and PBKDF2 password hashing
│── dependencies.py      # FastAPI auth dependencies (get_current_user, require_admin)
│── crud.py              # Database CRUD functions for products, users, and transactions
│── routes/
│   ├── auth_routes.py   # Endpoint routes for /auth/register, /auth/login, /auth/me
│   └── product_routes.py# Endpoint routes for /products CRUD operations
│── tests/
│   └── test_api.py      # Automated pytest unit and integration test suite
│── products.db          # SQLite database storage file (auto-generated on app run)
│── requirements.txt     # Python project dependencies
└── README.md            # Comprehensive project documentation
```

---

## 🚀 Environment Setup & Running the API

### Prerequisites
- Python 3.10 or higher installed on your system.

### 1. Installation
Clone or navigate to the project directory and create a Python virtual environment:

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Install required dependencies
pip install -r requirements.txt
```

### 2. Run API Server
Start the development server with live reload:

```bash
uvicorn main:app --reload
```

The API server will run at `http://127.0.0.1:8000`.

---

## 📑 Interactive Documentation

Once the server is running, access the interactive auto-generated documentation in your browser:

- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🔒 Authentication & Authorization Flow

1. **Register User**: Send a `POST` request to `/auth/register` specifying a `username`, `password`, and `role` (`"user"` or `"admin"`).
2. **Login**: Send a `POST` request to `/auth/login` to obtain your JWT `access_token`.
3. **Authorized Requests**: Include the JWT token in your HTTP request header:
   ```
   Authorization: Bearer <your_access_token>
   ```
4. **Admin Permissions**: Endpoints such as `DELETE /products/{product_id}` require a token generated for a user with `role: "admin"`. Standard users will receive a `403 Forbidden` error.

---

## 🔌 API Endpoint Specifications

| Method | Endpoint | Authorization | Description | Status Code |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/` | Public | Root health check & API info | `200 OK` |
| `POST` | `/auth/register` | Public | Register a new user (`user` or `admin`) | `201 Created` |
| `POST` | `/auth/login` | Public | Authenticate user & return JWT Token | `200 OK` |
| `GET` | `/auth/me` | User / Admin | Get profile of authenticated user | `200 OK` |
| `POST` | `/products` | User / Admin | Create a new product in inventory | `201 Created` |
| `GET` | `/products` | Public | List products (with optional `category`, `search`, pagination) | `200 OK` |
| `GET` | `/products/{id}` | Public | Retrieve a single product by ID | `200 OK` |
| `PUT` | `/products/{id}` | User / Admin | Update product details | `200 OK` |
| `DELETE` | `/products/{id}` | **Admin Only** | Delete a product from inventory | `200 OK` |

---

## 📝 Request & Response JSON Examples

### 1. User Registration (`POST /auth/register`)
**Request Body**:
```json
{
  "username": "john_admin",
  "password": "SecurePassword123!",
  "role": "admin"
}
```

**Response (201 Created)**:
```json
{
  "status": "success",
  "message": "User registered successfully",
  "data": {
    "id": 1,
    "username": "john_admin",
    "role": "admin"
  }
}
```

### 2. User Login (`POST /auth/login`)
**Request Body**:
```json
{
  "username": "john_admin",
  "password": "SecurePassword123!"
}
```

**Response (200 OK)**:
```json
{
  "status": "success",
  "message": "Login successful",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "role": "admin",
    "username": "john_admin"
  }
}
```

### 3. Create Product (`POST /products`)
**Headers**: `Authorization: Bearer <access_token>`  
**Request Body**:
```json
{
  "product_id": 101,
  "product_name": "Wireless Noise-Canceling Headphones",
  "description": "Premium over-ear Bluetooth headphones with active noise cancellation",
  "price": 249.99,
  "quantity": 40,
  "category": "Electronics"
}
```

**Response (201 Created)**:
```json
{
  "status": "success",
  "message": "Product created successfully",
  "data": {
    "product_id": 101,
    "product_name": "Wireless Noise-Canceling Headphones",
    "description": "Premium over-ear Bluetooth headphones with active noise cancellation",
    "price": 249.99,
    "quantity": 40,
    "category": "Electronics"
  }
}
```

### 4. Validation Error Response Example (400 Bad Request)
If a user submits a negative price (`"price": -50.0`):
```json
{
  "status": "error",
  "message": "Validation failed for request: body -> price: Input should be greater than 0",
  "details": [
    {
      "type": "greater_than",
      "loc": ["body", "price"],
      "msg": "Input should be greater than 0",
      "input": -50.0,
      "ctx": { "gt": 0 }
    }
  ]
}
```

### 5. Access Control Error Response Example (403 Forbidden)
If a non-admin user attempts `DELETE /products/101`:
```json
{
  "status": "error",
  "message": "Access denied: Admin role required for this action",
  "details": null
}
```

---

## 🧪 Running Automated Tests

Run the automated test suite using `pytest`:

```bash
python -m pytest tests/ -v
```

All tests execute in an isolated in-memory SQLite database environment to ensure reliability and repeatability.

---

## 📊 Summary of HTTP Status Codes

- `200 OK` – Request succeeded.
- `201 Created` – Resource successfully created.
- `400 Bad Request` – Validation failure, empty fields, or duplicate product ID.
- `401 Unauthorized` – Missing, invalid, or expired JWT token.
- `403 Forbidden` – Insufficient permissions (non-admin user attempting admin action).
- `404 Not Found` – Requested product or endpoint does not exist.
- `500 Internal Server Error` – Unhandled server failure.
