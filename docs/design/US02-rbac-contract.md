# US-02 Role-Based Access Control (RBAC) — Architecture & Integration Contract

**Document Version:** 1.0.0  
**Effective Date:** 27 October 2026  
**Traceability:** US-02 (#22, 5 SP), FR-16, NFR-SEC-01, NFR-SEC-02  
**Owner:** Member 1 (Trisha — Integration Lead & Scrum Master)  
**Target Consumers:** Member 4 (Admin Dashboard #45, Reports #46–#48, Audit Log #49, Security Verification #52), Member 2, Member 3  

---

## 1. Overview & Architectural Principle

US-02 establishes system-wide Role-Based Access Control (RBAC) across both backend and frontend layers. It enforces the canonical three-tier user role hierarchy defined in SRS §9.2 and SAD §3.9:

| Canonical Role | Value in DB / Token | Authorized Capabilities |
| :--- | :--- | :--- |
| **Administrator** | `'Admin'` | Full administrative access: user management, slot configuration, rate adjustments, reporting, system audit log, security verification. |
| **Operator** | `'Operator'` | Operational access: parking slot management, vehicle check-in/checkout, fee waiver processing, active occupancy inspection. |
| **Customer** | `'Customer'` | Self-service access: own vehicle registration, vehicle profile management, vehicle search, advance reservation booking, personal receipt inspection. |

---

## 2. Backend DRF Permission Classes

All classes are located in [`backend/accounts/permissions.py`](file:///c:/Users/Trisha%20V%20P/Vehicle-Parking-System-SE-MINI-PROJECT-1/backend/accounts/permissions.py).

### 2.1 Available Classes

| Class | Description | HTTP Challenge |
| :--- | :--- | :--- |
| `IsAuthenticatedAndActive` | Verifies user is authenticated and `status == 'active'` (rejects suspended/deactivated users). | 401 Unauthorized / 403 Forbidden |
| `IsAdmin` | Restricted strictly to users with `role == 'Admin'`. | 403 Forbidden |
| `IsOperator` | Restricted strictly to users with `role == 'Operator'`. | 403 Forbidden |
| `IsCustomer` | Restricted strictly to users with `role == 'Customer'`. | 403 Forbidden |
| `IsAdminOrOperator` | Grants access to both `Admin` and `Operator` staff. | 403 Forbidden |
| `has_roles(*roles)` | Factory returning custom permission class checking any of specified roles. | 403 Forbidden |
| `IsOwnerOrAdmin` | Object-level permission: allows if user is owner (`obj.owner` or `obj.user` or `obj`) or `role == 'Admin'`. | 403 Forbidden |
| `IsOwnerOrAdminOrOperator`| Object-level permission: allows if owner or staff member (`Admin`/`Operator`). | 403 Forbidden |

### 2.2 Error Envelope Guarantee

Consistent with the canonical shared error contract (US-31 / #51):

```json
{
  "error": "Permission denied. Required role(s): Admin.",
  "code": "PERMISSION_DENIED",
  "details": {
    "required_roles": ["Admin"],
    "current_role": "Customer"
  }
}
```

For unauthenticated requests:
```json
{
  "error": "Authentication credentials were not provided.",
  "code": "AUTHENTICATION_REQUIRED"
}
```

---

## 3. Frontend RBAC Integration

### 3.1 Utilities (`frontend/src/utils/rbac.js`)

```javascript
import { ROLES, isRoleAuthorized } from '../utils/rbac'

// Canonical Role Constants
ROLES.ADMIN = 'Admin'
ROLES.OPERATOR = 'Operator'
ROLES.CUSTOMER = 'Customer'

// Evaluation function
isRoleAuthorized(user.role, [ROLES.ADMIN]) // => boolean
```

### 3.2 Protected Route Guard (`frontend/src/routes/ProtectedRoute.jsx`)

Guards views against unauthenticated and unauthorized access:

```jsx
import { ProtectedRoute } from '../routes/ProtectedRoute'
import { ROLES } from '../utils/rbac'

// Example: Securing Member 4's Admin Dashboard
<ProtectedRoute allowedRoles={[ROLES.ADMIN]}>
  <AdminDashboard />
</ProtectedRoute>

// Example: Securing Operational Reports
<ProtectedRoute allowedRoles={[ROLES.ADMIN, ROLES.OPERATOR]}>
  <OccupancyReports />
</ProtectedRoute>
```

**Guard States Handled:**
1. **Loading State:** Renders accessible loading feedback while JWT/session hydrates; children are never exposed.
2. **Unauthenticated (401):** Displays styled error alert with prompt to log in; blocks access.
3. **Permission Denied (403):** Displays styled "Unauthorized Role" security card stating required roles vs assigned role.
4. **Authorized (200):** Renders protected child components.

---

## 4. Member 4 Handoff & Integration Instructions

Member 4 can immediately import and utilize these contracts across their assigned stories:

### For US-25 (Admin Dashboard #45):
```python
# In backend/reports/views.py
from accounts.permissions import IsAdmin

class AdminDashboardMetricsView(APIView):
    permission_classes = [IsAdmin]
    ...
```
```jsx
// In frontend/src/pages/AdminDashboard.jsx
import { ProtectedRoute } from '../routes/ProtectedRoute'
import { ROLES } from '../utils/rbac'

export default function AdminDashboardPage() {
  return (
    <ProtectedRoute allowedRoles={[ROLES.ADMIN]}>
      <AdminDashboardView />
    </ProtectedRoute>
  )
}
```

### For US-26 / US-27 / US-28 (Reports #46, #47, #48):
```python
from accounts.permissions import IsAdminOrOperator

class OccupancyReportView(APIView):
    permission_classes = [IsAdminOrOperator]
    ...
```

### For US-29 (System Audit Log #49):
```python
from accounts.permissions import IsAdmin

class AuditLogQueryView(APIView):
    permission_classes = [IsAdmin]
    ...
```

---

## 5. Verification & Test Evidence

1. **Backend Tests:** [`backend/accounts/tests/test_rbac.py`](file:///c:/Users/Trisha%20V%20P/Vehicle-Parking-System-SE-MINI-PROJECT-1/backend/accounts/tests/test_rbac.py)
   - 16 automated tests covering:
     - All 3 canonical roles against admin-only, operator-only, and customer-only views.
     - Multi-role union views (`IsAdminOrOperator`).
     - Object-level ownership checks (`IsOwnerOrAdmin`, `IsOwnerOrAdminOrOperator`).
     - Inactive/suspended user rejection.
     - Unauthenticated request rejection (401).
     - Result: `Ran 16 tests ... OK`.

2. **Frontend Tests:** [`frontend/tests/rbac.test.js`](file:///c:/Users/Trisha%20V%20P/Vehicle-Parking-System-SE-MINI-PROJECT-1/frontend/tests/rbac.test.js)
   - 7 test cases covering:
     - Role constants matching SRS §9.2.
     - Role authorization logic across valid, invalid, and edge-case roles.
     - Simulated route guard handling (Loading, 401 Unauthenticated, 403 Forbidden, 200 Authorized).
     - Client query/header tampering prevention.
   - Result: `75/75 passing` in full frontend test runner.

3. **Code Quality & Build:**
   - `oxlint`: 0 warnings, 0 errors across 32 files.
   - `vite build`: Succeeded in 1.22s.
   - `python manage.py check`: 0 issues.
