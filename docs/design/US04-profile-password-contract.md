# US-04 User Profile & Password Management — Architecture & Integration Contract

**Document Version:** 1.0.0  
**Effective Date:** 29 October 2026  
**Traceability:** US-04 (#24, 2 SP), FR-18, E1: Identity & Access Management  
**Owner:** Member 1 (Trisha — Integration Lead & Scrum Master)  
**Target Consumers:** Frontend Client, Member 4, Member 2, Member 3  

---

## 1. Overview & Architectural Scope

US-04 delivers self-service profile inspection, editable contact details, and secure password management for authenticated users across all roles (`Admin`, `Operator`, `Customer`).

### Acceptance Criteria
- **AC-1:** Given an authenticated user, When updating editable profile details (contact number, name), Then valid fields are updated and persisted with HTTP 200.
- **AC-2:** Given a user supplying valid current password and compliant new password, When password change is submitted, Then the new password is encrypted and persisted successfully.
- **AC-3:** Given an incorrect current password or weak new password violating complexity rules, When change is submitted, Then the request is rejected with HTTP 400 Bad Request.

---

## 2. API Endpoints & Contracts

### 2.1 Profile Inspection & Update (`GET`, `PATCH`, `PUT /api/auth/profile/` or `/api/auth/me/`)

- **Authentication:** Bearer token required (`IsAuthenticatedAndActive`). Suspended users rejected with HTTP 403.
- **Request Body (`PATCH`):**
```json
{
  "first_name": "Jane",
  "last_name": "Doe",
  "phone_number": "+1 (555) 123-4567",
  "contact_number": "+1 (555) 123-4567",
  "email": "jane.doe@example.com"
}
```
- **Response (HTTP 200 OK):**
```json
{
  "id": 1,
  "username": "customer1",
  "email": "jane.doe@example.com",
  "first_name": "Jane",
  "last_name": "Doe",
  "phone_number": "+1 (555) 123-4567",
  "contact_number": "+1 (555) 123-4567",
  "role": "Customer",
  "status": "active"
}
```
- **Security Guarantees:**
  - `role`, `status`, `username`, `id` are read-only and immutable via profile endpoints (privilege escalation prevention).
  - Duplicate emails are rejected with HTTP 400 (`{"email": ["A user with this email address already exists."]}`).

### 2.2 Password Change (`POST /api/auth/password/change/` or `/api/auth/change-password/`)

- **Authentication:** Bearer token required (`IsAuthenticatedAndActive`).
- **Request Body:**
```json
{
  "current_password": "OldPassword123!",
  "new_password": "NewSecurePassword456@",
  "new_password_confirm": "NewSecurePassword456@"
}
```
- **Response (HTTP 200 OK):**
```json
{
  "message": "Password changed successfully. Your active sessions have been updated."
}
```
- **Validation Rules & Error Envelopes (HTTP 400):**
  - Incorrect current password: `{"current_password": ["Current password is incorrect."]}`
  - Password complexity failure: `{"new_password": ["Password must contain at least one uppercase letter..."]}`
  - New password equals current password: `{"new_password": ["New password cannot be the same as the current password."]}`
  - Confirmation mismatch: `{"new_password_confirm": ["New passwords do not match."]}`
  - Session revocation: Increments `user.token_version += 1` to immediately invalidate all outstanding JWT access/refresh tokens.

---

## 3. Frontend Implementation

- **Page Component:** [`frontend/src/pages/Profile.jsx`](file:///c:/Users/Trisha%20V%20P/Vehicle-Parking-System-SE-MINI-PROJECT-1/frontend/src/pages/Profile.jsx)
- **Validation Utility:** [`frontend/src/utils/profileValidation.js`](file:///c:/Users/Trisha%20V%20P/Vehicle-Parking-System-SE-MINI-PROJECT-1/frontend/src/utils/profileValidation.js)
- **Auth Shell Integration:** [`frontend/src/components/AuthenticatedView.jsx`](file:///c:/Users/Trisha%20V%20P/Vehicle-Parking-System-SE-MINI-PROJECT-1/frontend/src/components/AuthenticatedView.jsx) under `activePage === 'account'`.

---

## 4. Verification & Test Summary

- **Backend:** 11 focused test cases in [`backend/accounts/tests/test_profile_password.py`](file:///c:/Users/Trisha%20V%20P/Vehicle-Parking-System-SE-MINI-PROJECT-1/backend/accounts/tests/test_profile_password.py). All 75 accounts app tests passing.
- **Frontend:** 12 focused test cases in [`frontend/tests/profile.test.js`](file:///c:/Users/Trisha%20V%20P/Vehicle-Parking-System-SE-MINI-PROJECT-1/frontend/tests/profile.test.js). All 87 frontend unit tests passing. Production build verified clean.

