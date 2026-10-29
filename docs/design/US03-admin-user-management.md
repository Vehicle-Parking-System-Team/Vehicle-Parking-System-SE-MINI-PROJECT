# US-03 Admin User Account Management Contract & Design

Issue: [#23 — Admin User Account Management](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/issues/23)  
Functional Owner: Member 1  
Parent Epic: #2 (E1 – Identity & Access Management)  
Requirement: FR-17  

---

## 1. Overview & Acceptance Criteria

US-03 enables administrators to manage system user accounts, enforce lifecycle status changes immediately, and securely provision Operator and Customer accounts. Admin-created accounts are deliberately limited to those two roles; privileged Admin accounts are provisioned separately. The PATCH endpoint also cannot promote existing accounts to Admin.

- **AC-1:** Given valid administrator credentials, When creating a new operator or customer account with required fields, Then the account is created and stored with hashed password.
- **AC-2:** Given an existing user account, When an administrator updates account status (`active`/`suspended`/`deactivated`), Then the updated status is enforced immediately on subsequent requests.
- **AC-3:** Given duplicate email or username input, When an account creation request is submitted, Then the system returns HTTP 409 Conflict with a clear validation message. Username and non-empty email uniqueness is enforced case-insensitively by database constraints as well as request validation; integrity conflicts detected after a concurrent insert are translated to HTTP 409.

---

## 2. API Endpoints

### 2.1 List & Filter Users
- **Route:** `GET /api/auth/users/`
- **Permission:** `IsAdmin`
- **Query Parameters:**
  - `role`: Filter by canonical role (`Admin`, `Operator`, `Customer`).
  - `status`: Filter by status (`active`, `suspended`, `deactivated`).
  - `search`: Case-insensitive substring search across `username` and `email`.
- **Response (200 OK):**
```json
[
  {
    "id": 1,
    "username": "operator_joe",
    "email": "joe@parking.local",
    "role": "Operator",
    "status": "active",
    "is_active": true,
    "date_joined": "2026-10-28T12:00:00Z"
  }
]
```

### 2.2 Create User Account
- **Route:** `POST /api/auth/users/`
- **Permission:** `IsAdmin`
- **Request Body:**
```json
{
  "username": "operator_jane",
  "email": "jane@parking.local",
  "password": "SecurePassword123!",
  "role": "Operator"
}
```
- **Responses:**
  - `201 Created`: User created with hashed password and active status.
  - `400 Bad Request`: Password fails policy or required field missing.
  - `409 Conflict`: Username or email already registered.

### 2.3 Retrieve User Details
- **Route:** `GET /api/auth/users/{id}/`
- **Permission:** `IsAdmin`
- **Response (200 OK):** User account details.

### 2.4 Update User Status or Role
- **Route:** `PATCH /api/auth/users/{id}/`
- **Permission:** `IsAdmin`
- **Request Body (Partial):**
```json
{
  "status": "suspended"
}
```
- **Responses:**
  - `200 OK`: Account updated. When status changes to `suspended` or `deactivated`, `token_version` is atomically incremented, immediately revoking all outstanding JWT tokens on subsequent requests.
  - `400 Bad Request`: Self-lockout attempted, unsupported creation role supplied, or attempt to suspend/deactivate/demote the last active administrator. The last-admin check and account update execute in one transaction with row locks on databases that support `SELECT FOR UPDATE`. Role updates may switch between Operator and Customer only; promotion to Admin is rejected by the API and hidden from the UI.
  - `404 Not Found`: Target user does not exist.

---

## 3. Integration Contract for Member 4 (US-25 & US-29)

To support Member 4's **US-25 (Admin Dashboard)** and **US-29 (Security Audit Log)**, `backend/accounts/events.py` defines the canonical event schema and dispatcher:

```python
from accounts.events import UserAccountChangeEvent, dispatch_user_account_change
```

### Event Payload Schema (`UserAccountChangeEvent`):
- `actor_id`: (int) ID of the administrator making the change.
- `actor_username`: (str) Username of the administrator.
- `target_user_id`: (int) ID of the account being modified.
- `target_username`: (str) Username of the modified account.
- `event_type`: (str) `'USER_CREATED'`, `'STATUS_CHANGED'`, `'ROLE_CHANGED'`, or `'ACCOUNT_UPDATED'`.
- `previous_state`: (dict) Key-value pairs before modification.
- `new_state`: (dict) Key-value pairs after modification.
- `timestamp`: (str) ISO 8601 formatted timestamp.

`dispatch_user_account_change` emits the `user_account_changed` Django signal using robust dispatch and writes a structured log entry. Receivers are best-effort: failures are logged without turning a persisted account mutation into an HTTP 500. Guaranteed delivery would require a transactional outbox and is outside the current US-03 contract. Member 4 can connect a receiver to `accounts.events.user_account_changed`. This is an integration seam, not a claim that the dashboard or persistent audit-log feature is implemented here; durable audit storage remains part of US-29.
