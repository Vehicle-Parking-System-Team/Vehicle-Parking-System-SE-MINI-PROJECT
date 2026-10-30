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
  "message": "Password changed successfully."
}
```
- **Validation Rules & Error Envelopes (HTTP 400):**
  - Incorrect current password: `{"current_password": ["Current password is incorrect."]}`
  - Password complexity failure: `{"new_password": ["Password must contain at least one uppercase letter..."]}`
  - New password equals current password: `{"new_password": ["New password cannot be the same as the current password."]}`
  - Confirmation mismatch: `{"new_password_confirm": ["New passwords do not match."]}`
  - Session revocation: Password changes increment `user.token_version`; requests using access or refresh tokens with the prior version are rejected. The frontend clears its local session and returns the user to sign-in after a successful password change.
  - Phone format: The backend validates both `phone_number` and the `contact_number` compatibility alias. Values may contain digits, spaces, `+`, `-`, and parentheses, up to 20 characters; blank is allowed. The model and migration define an empty-string database default for legacy inserts that omit this optional field.

---

## 3. Frontend Implementation

- **Page Component:** [`frontend/src/pages/Profile.jsx`](../../frontend/src/pages/Profile.jsx)
- **Validation Utility:** [`frontend/src/utils/profileValidation.js`](../../frontend/src/utils/profileValidation.js)
- **Auth Shell Integration:** [`frontend/src/components/AuthenticatedView.jsx`](../../frontend/src/components/AuthenticatedView.jsx) under `activePage === 'account'`.

---

## 4. Verification & Test Summary

- **Backend:** Regression tests cover profile reads/updates, role/status immutability, duplicate email rejection, malformed phone-number rejection for both API field names, optional blank phone numbers, password-policy failures, and rejection of pre-change access and refresh tokens.
- **Frontend:** Validation and profile/password request behavior are covered by [`frontend/tests/profile.test.js`](../../frontend/tests/profile.test.js).
- **Execution status:** See the current PR checks for the authoritative backend/frontend CI and security results; do not reuse test counts from earlier revisions.

