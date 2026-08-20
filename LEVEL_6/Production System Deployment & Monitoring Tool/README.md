# Production System Deployment & Monitoring Tool

A Python-based Production System Deployment & Monitoring Tool built with **FastAPI**, **SQLAlchemy**, **PyMySQL**, and **APScheduler**. Designed for DevOps and Site Reliability Engineering (SRE) teams to track application health, monitor uptime, capture errors, evaluate configurable threshold rules, trigger multi-channel alerts, maintain immutable audit logs, and automate daily/weekly reporting in JSON, CSV, and PDF formats.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture & Workflow](#architecture--workflow)
3. [MySQL Database Setup & Configuration](#mysql-database-setup--configuration)
4. [Environment Variables](#environment-variables)
5. [Installation](#installation)
6. [How to Run the Service](#how-to-run-the-service)
7. [Health Check Logic](#health-check-logic)
8. [Periodic Monitoring Scheduler](#periodic-monitoring-scheduler)
9. [Per-Service Monitoring Intervals](#per-service-monitoring-intervals)
10. [Error & Exception Logging](#error--exception-logging)
11. [Server Downtime Tracking](#server-downtime-tracking)
12. [Alert Threshold System & Configurable Rules](#alert-threshold-system--configurable-rules)
13. [Alert Generation Methods & Deduplication](#alert-generation-methods--deduplication)
14. [Uptime Calculation & Performance Metrics](#uptime-calculation--performance-metrics)
15. [Reporting Workflows & Export Automation](#reporting-workflows--export-automation)
16. [Persistent Audit Logging](#persistent-audit-logging)
17. [Complete REST API Reference](#complete-rest-api-reference)
18. [Database Schema (6 Tables)](#database-schema-6-tables)
19. [Step-by-Step Practical Usage Guide](#step-by-step-practical-usage-guide)

---

## Project Overview

In modern cloud infrastructures, continuous visibility into service availability, latency degradation, and error surges is essential. This tool provides a production-grade backend engine that continuously probes registered HTTP services, evaluates custom SRE thresholds, prevents alert spam via deduplication, generates operational metrics and reports, and records every system and configuration change in an immutable MySQL audit log.

### Key Capabilities:
- **Continuous HTTP Health Probing**: Response latency measurement, status validation, and deep failure categorization (DNS, SSL, timeout, connection drop).
- **Per-Service Interval Execution**: Fine-grained check intervals per service handled in background scheduling cycles.
- **Runtime-Configurable Rules**: Create, update, or toggle response time, consecutive failure, and error frequency thresholds via API without restarting the server.
- **Multi-Channel Alert Dispatching**: Alerts are logged to the console, appended to `logs/monitoring.log`, saved in MySQL `alerts`, and audited.
- **Uptime & Performance Analytics**: Daily and 7-day weekly uptime percentages calculated strictly using `(Healthy Checks / Total Checks) * 100`.
- **Automated Health Reports**: Daily summaries, 7-day weekly summaries, service comparisons, with JSON, CSV, and PDF export capabilities.
- **Enterprise Configuration Auditing**: Every interval, timeout, status expectation, or rule modification is logged in `audit_logs`.

---

## Architecture & Workflow

```
+-----------------------------------------------------------------------------------+
|                               FastAPI Application                                 |
|                                                                                   |
|  +--------------------+   +---------------------+   +--------------------------+  |
|  | /api/services      |   | /api/health         |   | /api/rules               |  |
|  | /api/metrics       |   | /api/reports        |   | /api/alerts & /api/logs  |  |
|  +---------+----------+   +----------+----------+   +------------+-------------+  |
+------------|-------------------------|---------------------------|----------------+
             |                         |                           |
             v                         v                           v
+-----------------------------------------------------------------------------------+
|                            APScheduler Background Engine                          |
|             (Evaluates each service's check_interval_seconds every cycle)         |
+--------------------------------------+--------------------------------------------+
                                       |
                                       v
+-----------------------------------------------------------------------------------+
|                                Health Checker Engine                              |
|           • Non-blocking HTTP GET with timeout enforcement                        |
|           • Response latency measurement (ms)                                     |
|           • Failure categorization (DNS, SSL, Timeout, Connection, 4xx/5xx)       |
+--------------------------------------+--------------------------------------------+
                                       |
                                       v
+-----------------------------------------------------------------------------------+
|                                Alert & Rule Engine                                |
|           • Evaluates active RESPONSE_TIME, CONSECUTIVE_FAILURES, ERROR_FREQ rules|
|           • Generates PASS/FAIL audit records for every evaluation                |
|           • Deduplicates active alerts to prevent alert storming                  |
+-------------------+------------------+---------------------------+----------------+
                    |                  |                           |
                    v                  v                           v
         +--------------------+  +---------------+  +-------------------------------+
         | Console & Log File |  | MySQL Storage |  | Reports Export (JSON/CSV/PDF) |
         | logs/monitoring.log|  |   (6 Tables)  |  |           reports/            |
         +--------------------+  +---------------+  +-------------------------------+
```

---

## MySQL Database Setup & Configuration

### Automatic Database Creation
On application startup, the application connects to your MySQL server (via PyMySQL) and automatically executes:
```sql
CREATE DATABASE IF NOT EXISTS `production_monitoring` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```
After the database exists, SQLAlchemy automatically initializes all **6 required tables** (`services`, `health_checks`, `error_logs`, `monitoring_rules`, `alerts`, `audit_logs`).

### Manual Database Creation (Fallback)
If your configured MySQL user does not have `CREATE DATABASE` privileges, execute the following in your MySQL CLI or workbench before starting the application:
```sql
CREATE DATABASE production_monitoring;
```

---

## Environment Variables

Environment variables are loaded securely via `python-dotenv`. Credentials and secrets reside in `.env`, which is included in `.gitignore` and never committed to version control.

Use the provided `.env.example` as a reference:

```bash
# MySQL Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password_here
DB_NAME=production_monitoring

# Application Settings
APP_PORT=8000
APP_HOST=0.0.0.0
LOG_LEVEL=INFO

# Monitoring Scheduler Settings
SCHEDULER_INTERVAL_SECONDS=60

# Optional Alert Notification Settings
ALERT_EMAIL_ENABLED=false
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=alerts@example.com
SMTP_PASSWORD=smtp_password_here
ALERT_RECEIVER_EMAIL=devops@example.com
```

---

## Installation

### Prerequisites
- Python 3.10 or above
- MySQL 8.0+ / MariaDB

### Steps
1. Clone or open the project directory:
   ```bash
   cd production-monitoring-tool
   ```

2. Create and activate a Python virtual environment (recommended):
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   ```

3. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create your `.env` file from the template and configure your MySQL credentials:
   ```bash
   cp .env.example .env
   ```

---

## How to Run the Service

Start the FastAPI application with Uvicorn:

```bash
uvicorn main:app --reload
```

The service will start at `http://127.0.0.1:8000`.

### Interactive API Documentation
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## Health Check Logic

The Health Checker engine (`health_checker.py`) performs non-blocking HTTP probes against registered endpoints:

1. **Latency Measurement**: Accurately measures response time from connection dispatch to full body receipt using `time.perf_counter()`.
2. **Status Validation**: Compares the received HTTP status against the service's `expected_status_code` (e.g., 200).
3. **Granular Exception Handling & Error Categorization**:
   - `requests.exceptions.Timeout` $\to$ Categorized as `HTTP_TIMEOUT` (Severity: `ERROR`).
   - `requests.exceptions.SSLError` $\to$ Categorized as `SSL_ERROR` (Severity: `ERROR`).
   - DNS resolution failure (`getaddrinfo` / `gaierror`) $\to$ Categorized as `DNS_ERROR` (Severity: `CRITICAL`).
   - Connection dropped or refused $\to$ Categorized as `CONNECTION_ERROR` (Severity: `CRITICAL`).
   - Status code mismatch (e.g. 500 or 404) $\to$ Categorized as `HTTP_STATUS_MISMATCH` (Severity: `WARNING`/`ERROR`).
   - Unhandled exception $\to$ Categorized as `APP_EXCEPTION` (Severity: `CRITICAL`).
4. **Persistent History**: Every check attempt creates an immutable record in `health_checks`.

---

## Periodic Monitoring Scheduler

The periodic scheduler (`scheduler.py`) uses APScheduler running in the background lifecycle of FastAPI:

- The scheduler loop executes a dispatch check every `SCHEDULER_INTERVAL_SECONDS` (default: 60s).
- It opens an isolated database session and queries all active services (`is_active = TRUE`).
- Safe execution ensures that if any single service endpoint experiences a failure or hang, it does not block or impact subsequent service checks.

---

## Per-Service Monitoring Intervals

Each service maintains its own configurable `check_interval_seconds` field:

$$\text{Due Check Condition} = (\text{last\_check\_at IS NULL}) \lor (\text{now} - \text{last\_check\_at} \ge \text{check\_interval\_seconds})$$

- Services with `check_interval_seconds = 10` are checked every 10 seconds.
- Services with `check_interval_seconds = 300` are checked every 5 minutes.
- **Runtime Modifiable**: Updating `check_interval_seconds` via `PUT /api/services/{id}` takes effect immediately without requiring code modifications or server restarts.

---

## Error & Exception Logging

Errors are tracked persistently across multiple layers:

1. **MySQL Persistence (`error_logs` table)**:
   - Stores timestamp, service ID, error message, severity (`INFO`, `WARNING`, `ERROR`, `CRITICAL`), source category, and stack trace.
2. **Rotating File Logging (`logs/monitoring.log`)**:
   - 10MB per file with automatic rotation (up to 5 backup archives).
3. **Console Logging**:
   - Structured standard output format for container log scrapers (Docker, Fluentd, CloudWatch).
4. **Global Unhandled Exception Interceptor**:
   - FastAPI global exception handler catches unhandled 500 errors, logs full stack traces to `error_logs` and `audit_logs`, and returns a structured JSON payload without crashing the monitoring service.

---

## Server Downtime Tracking

Downtime tracking uses consecutive health check results:

- **Consecutive Failures**: Incremented by 1 on each failed check; reset to 0 upon a successful healthy check.
- **Status Progression**:
  - 0 Failures: `HEALTHY`
  - 1–2 Failures: `DEGRADED`
  - $\ge 3$ Failures (or custom threshold): `DOWN`
- **Downtime Duration Calculation**: Approximated by multiplying consecutive failed checks by the service check interval.
- **Alert Generation**: Breaching the consecutive failure threshold triggers a `SERVICE_DOWN` alert.

---

## Alert Threshold System & Configurable Rules

Rules (`monitoring_rules` table) define thresholds evaluated after each health check:

| Rule Type | Threshold Metric | Example Value | Description |
|---|---|---|---|
| `RESPONSE_TIME` | Milliseconds ($ms$) | `5000.0` | Triggers alert when check latency exceeds threshold. |
| `CONSECUTIVE_FAILURES` | Failure count | `3.0` | Triggers `SERVICE_DOWN` alert when consecutive failures reach threshold. |
| `ERROR_FREQUENCY` | Error count in window | `10.0` (in 60 mins) | Triggers alert when error count within `time_window_minutes` exceeds limit. |

- **Scope**: Rules can be global (`service_id = NULL`) or targeted to a specific service (`service_id = {id}`).
- **Audit Logging**: Every rule evaluation records a `RULE_EVALUATED` audit record in `audit_logs` for **both PASS and FAIL** outcomes.
- **Runtime Modification**: Rules can be created, updated, or toggled on/off at runtime via REST endpoints (`/api/rules`).

---

## Alert Generation Methods & Deduplication

### Multi-Channel Dispatching
When a rule threshold is breached:
1. **Database Persistence**: An alert record is created in the `alerts` table (`is_resolved = FALSE`).
2. **Log File**: Written to `logs/monitoring.log` with `[ALERT - CRITICAL/WARNING]`.
3. **Console**: Displayed in standard output.
4. **Audit Trail**: `ALERT_TRIGGERED` action is added to `audit_logs`.
5. **Email Notification (Optional)**: If `ALERT_EMAIL_ENABLED=true`, sends an SMTP email notification.

### Alert Deduplication
To prevent alert storming, the alert manager verifies whether an unresolved alert (`is_resolved = FALSE`) already exists for the same `service_id` and `alert_type`. If an active alert exists, repeated duplicate notifications are suppressed. Once resolved via `POST /api/alerts/{id}/resolve`, new alerts can trigger if issues recur.

---

## Uptime Calculation & Performance Metrics

### Mathematical Formula
$$\text{Uptime Percentage} = \left( \frac{\text{Healthy Checks}}{\text{Total Checks}} \right) \times 100$$

### Operational Metrics Endpoint (`GET /api/metrics`)
Provides real-time visibility into:
- System-wide daily & weekly uptime %
- Active, healthy, degraded, and down service counts
- Service-specific metrics (24h error count, 24h alert count, active alert count, average latency)
- 7-day historical daily breakdown (date, total checks, healthy checks, uptime %, avg latency, errors)

---

## Reporting Workflows & Export Automation

### Generated Reports
1. **Daily System Health Report (`GET /api/reports/daily`)**: 24-hour summary of all services, uptime %, error counts, and alert counts.
2. **Weekly Monitoring Summary (`GET /api/reports/weekly`)**: 7-day aggregation, daily breakdowns, and operational trend evaluation (`EXCELLENT`, `STABLE`, `DEGRADING`).
3. **Service Performance Comparison (`GET /api/reports/compare`)**: Comparative ranking of all services by uptime and latency.

### Export Formats (`reports/` directory)
- **JSON Export**: `GET /api/reports/export/json?report_type=daily|weekly|compare`
- **CSV Export**: `GET /api/reports/export/csv?report_type=daily|weekly|compare`
- **PDF Export**: `GET /api/reports/export/pdf?report_type=daily|weekly|compare` (Built with ReportLab, featuring styled tables, color-coded status, and metrics).

---

## Persistent Audit Logging

Every configuration update and operational event is immutably logged into `audit_logs`:

| Action Constant | Entity Type | Details Recorded |
|---|---|---|
| `SERVICE_CREATED` | `SERVICE` | Registered service URL, interval, expected code, timeout |
| `SERVICE_UPDATED` | `SERVICE` | Name or URL changes |
| `MONITORING_INTERVAL_UPDATED` | `SERVICE` | Old interval $\to$ New interval |
| `TIMEOUT_UPDATED` | `SERVICE` | Old timeout $\to$ New timeout |
| `EXPECTED_STATUS_UPDATED` | `SERVICE` | Old expected code $\to$ New expected code |
| `SERVICE_ACTIVATED` | `SERVICE` | Service resumed (`is_active = True`) |
| `SERVICE_DEACTIVATED` | `SERVICE` | Service paused (`is_active = False`) |
| `SERVICE_DELETED` | `SERVICE` | Deleted service ID and name |
| `RULE_CREATED` | `RULE` | Rule type, threshold, window, target service |
| `RULE_UPDATED` | `RULE` | Rule metadata updates |
| `RULE_THRESHOLD_UPDATED` | `RULE` | Old threshold $\to$ New threshold |
| `RULE_TIME_WINDOW_UPDATED` | `RULE` | Old window $\to$ New window |
| `RULE_ENABLED` / `RULE_DISABLED` | `RULE` | Rule toggle state |
| `RULE_DELETED` | `RULE` | Deleted rule ID |
| `RULE_EVALUATED` | `RULE` | PASS / FAIL evaluation metrics vs threshold |
| `ALERT_TRIGGERED` | `ALERT` | Triggered alert type, severity, message |
| `ALERT_RESOLVED` | `ALERT` | Resolved alert ID and notes |
| `HEALTH_CHECK_EXECUTED` | `HEALTH_CHECK` | Health check latency, status, result |
| `SCHEDULER_STARTUP` | `SCHEDULER` | Scheduler startup timestamp & cycle interval |
| `SCHEDULER_SHUTDOWN` | `SCHEDULER` | Safe scheduler shutdown timestamp |
| `SYSTEM_EXCEPTION` | `SYSTEM` | Unhandled exception endpoint and error details |

Query audit logs at `GET /api/logs/audit`.

---

## Complete REST API Reference

### Service Management
- `POST /api/services` — Register a new monitored service.
- `GET /api/services` — List all monitored services.
- `GET /api/services/{id}` — Get service details by ID.
- `PUT /api/services/{id}` — Update service configuration (interval, timeout, expected status, active state).
- `DELETE /api/services/{id}` — Deregister and delete a service.

### Health Monitoring
- `GET /api/health/status` — Get real-time status overview of all services.
- `POST /api/health/check/{id}` — Trigger an on-demand manual health check.
- `GET /api/health/history/{id}` — Get historical health check records for a service.

### Alert Management
- `GET /api/alerts` — Query triggered alerts (filters: `service_id`, `is_resolved`, `severity`).
- `GET /api/alerts/{id}` — Get alert details by ID.
- `POST /api/alerts/{id}/resolve` — Mark an active alert as resolved.

### Monitoring Rules
- `POST /api/rules` — Create a monitoring rule (`RESPONSE_TIME`, `CONSECUTIVE_FAILURES`, `ERROR_FREQUENCY`).
- `GET /api/rules` — List all monitoring rules.
- `GET /api/rules/{id}` — Get rule details by ID.
- `PUT /api/rules/{id}` — Update rule parameters (threshold, time window).
- `PATCH /api/rules/{id}/toggle` — Enable or disable a rule.
- `DELETE /api/rules/{id}` — Delete a monitoring rule.

### Performance Metrics
- `GET /api/metrics` — Get system-wide and service-level operational metrics.
- `GET /api/metrics/{id}` — Get service-specific operational metrics with 7-day daily breakdown.

### Reports & Exports
- `GET /api/reports/daily` — Generate Daily System Health Report (JSON).
- `GET /api/reports/weekly` — Generate Weekly Monitoring Summary (JSON).
- `GET /api/reports/compare` — Generate Service Performance Comparison (JSON).
- `GET /api/reports/export/json` — Export report as JSON file.
- `GET /api/reports/export/csv` — Export report as CSV file.
- `GET /api/reports/export/pdf` — Export report as formatted PDF document.

### Logs & Audits
- `GET /api/logs/errors` — Query captured error and exception logs.
- `GET /api/logs/audit` — Query immutable audit trail logs.

---

## Database Schema (6 Tables)

```text
+--------------------------------------------------------------------------------+
|                                    services                                    |
+------------------------+--------------+----------------------------------------+
| id (PK)                | INT (AI)     | Unique service identifier               |
| name                   | VARCHAR(100) | Unique human-readable service name     |
| url                    | VARCHAR(255) | Endpoint URL to probe                  |
| check_interval_seconds | INT          | Probing interval (default: 60)         |
| expected_status_code   | INT          | Expected HTTP status (default: 200)    |
| timeout_seconds        | INT          | Request timeout in seconds (default: 5)|
| is_active              | BOOLEAN      | Monitoring active status (default: 1)  |
| consecutive_failures   | INT          | Count of consecutive failed checks     |
| current_status         | VARCHAR(20)  | HEALTHY, DEGRADED, DOWN, UNKNOWN       |
| last_check_at          | DATETIME     | Timestamp of last executed probe       |
| created_at             | DATETIME     | Creation timestamp                     |
| updated_at             | DATETIME     | Last modification timestamp            |
+------------------------+--------------+----------------------------------------+

+--------------------------------------------------------------------------------+
|                                 health_checks                                  |
+--------------------+--------------+--------------------------------------------+
| id (PK)            | INT (AI)     | Unique check identifier                    |
| service_id (FK)    | INT          | Foreign key -> services.id (CASCADE)       |
| status_code        | INT          | Received HTTP status code (or NULL)        |
| response_time_ms   | FLOAT        | Response latency in milliseconds           |
| is_healthy         | BOOLEAN      | True if healthy, False otherwise           |
| error_message      | TEXT         | Error description if unhealthy             |
| checked_at         | DATETIME     | Probe execution timestamp                  |
+--------------------+--------------+--------------------------------------------+

+--------------------------------------------------------------------------------+
|                                  error_logs                                    |
+--------------------+--------------+--------------------------------------------+
| id (PK)            | INT (AI)     | Unique error identifier                    |
| service_id (FK)    | INT          | Foreign key -> services.id (SET NULL)      |
| error_message      | TEXT         | Error or exception message                 |
| severity           | VARCHAR(20)  | INFO, WARNING, ERROR, CRITICAL             |
| source             | VARCHAR(100) | HTTP_TIMEOUT, DNS_ERROR, SSL_ERROR, etc.   |
| stack_trace        | TEXT         | Detailed exception stack trace             |
| timestamp          | DATETIME     | Timestamp when error occurred              |
+--------------------+--------------+--------------------------------------------+

+--------------------------------------------------------------------------------+
|                               monitoring_rules                                 |
+---------------------+--------------+-------------------------------------------+
| id (PK)             | INT (AI)     | Unique rule identifier                    |
| name                | VARCHAR(100) | Descriptive rule name                     |
| service_id (FK)     | INT          | FK -> services.id (NULL for global)       |
| rule_type           | VARCHAR(50)  | RESPONSE_TIME, CONSECUTIVE_FAILURES, etc. |
| threshold_value     | FLOAT        | Numeric threshold limit                   |
| time_window_minutes | INT          | Evaluation time window in minutes         |
| is_enabled          | BOOLEAN      | Rule active toggle                        |
| created_at          | DATETIME     | Creation timestamp                        |
| updated_at          | DATETIME     | Modification timestamp                    |
+---------------------+--------------+-------------------------------------------+

+--------------------------------------------------------------------------------+
|                                    alerts                                      |
+--------------------+--------------+--------------------------------------------+
| id (PK)            | INT (AI)     | Unique alert identifier                    |
| service_id (FK)    | INT          | Foreign key -> services.id (CASCADE)       |
| rule_id (FK)       | INT          | FK -> monitoring_rules.id (SET NULL)       |
| alert_type         | VARCHAR(50)  | SERVICE_DOWN, RESPONSE_TIME_EXCEEDED, etc. |
| severity           | VARCHAR(20)  | WARNING, CRITICAL                          |
| message            | TEXT         | Alert notification message                 |
| is_resolved        | BOOLEAN      | False if active, True if resolved          |
| triggered_at       | DATETIME     | Trigger timestamp                          |
| resolved_at        | DATETIME     | Resolution timestamp (or NULL)             |
+--------------------+--------------+--------------------------------------------+

+--------------------------------------------------------------------------------+
|                                  audit_logs                                    |
+--------------------+--------------+--------------------------------------------+
| id (PK)            | INT (AI)     | Unique audit identifier                    |
| action             | VARCHAR(100) | Specific audit action constant             |
| entity_type        | VARCHAR(50)  | SERVICE, RULE, ALERT, HEALTH_CHECK, etc.   |
| entity_id          | INT          | ID of the modified entity                  |
| service_id (FK)    | INT          | Related service ID (if applicable)         |
| details            | TEXT         | Detailed audit record of the event         |
| event_type         | VARCHAR(20)  | INFO, AUDIT, ALERT, ERROR                  |
| timestamp          | DATETIME     | Audit event timestamp                      |
+--------------------+--------------+--------------------------------------------+
```

---

## Step-by-Step Practical Usage Guide

### 1. Register a Monitored Service
```bash
curl -X POST "http://127.0.0.1:8000/api/services" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Auth API Service",
       "url": "https://httpbin.org/status/200",
       "check_interval_seconds": 30,
       "expected_status_code": 200,
       "timeout_seconds": 5,
       "is_active": true
     }'
```

### 2. Trigger an Immediate Manual Health Check
```bash
curl -X POST "http://127.0.0.1:8000/api/health/check/1"
```

### 3. Update Monitoring Configuration (with Automatic Audit Trail)
```bash
curl -X PUT "http://127.0.0.1:8000/api/services/1" \
     -H "Content-Type: application/json" \
     -d '{
       "check_interval_seconds": 15,
       "timeout_seconds": 3
     }'
```

### 4. Create a Custom Threshold Rule
```bash
curl -X POST "http://127.0.0.1:8000/api/rules" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Strict Latency Limit",
       "service_id": 1,
       "rule_type": "RESPONSE_TIME",
       "threshold_value": 1500.0,
       "time_window_minutes": 60,
       "is_enabled": true
     }'
```

### 5. Check Performance & Uptime Metrics
```bash
curl -X GET "http://127.0.0.1:8000/api/metrics/1"
```

### 6. Export Health Reports
```bash
# Export PDF Report
curl -X GET "http://127.0.0.1:8000/api/reports/export/pdf?report_type=daily" --output daily_report.pdf

# Export CSV Report
curl -X GET "http://127.0.0.1:8000/api/reports/export/csv?report_type=compare" --output comparison.csv
```

### 7. View Audit Logs
```bash
curl -X GET "http://127.0.0.1:8000/api/logs/audit?limit=20"
```
