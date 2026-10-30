# US-07 — Vehicle Search & Live Parking Status Implementation

- **User Story:** US-07 (#27) — Search vehicle and current status
- **Parent Epic:** E2 (#15) — Vehicle Management
- **Owner:** Member 1
- **Primary Requirement:** FR-11 (Functional Requirement 11)
- **Performance NFRs:** NFR-PERF-01 (< 500ms p95), NFR-PERF-03 (Indexed queries, < 200ms)
- **Test Identifiers:** `TC-UC02-API-001`, `TC-UC02-API-002`, `TC-UC02-UNIT-001`

---

## 1. Overview & Scope

US-07 delivers an instant vehicle search capability by license plate and inspects its real-time parking status across the facility. It directly integrates with:
- **US-05 (Vehicle Registration):** Searches registered vehicles by plate number.
- **US-06 (Vehicle Profile Management):** Allows users to transition directly from search results to full vehicle profile viewing and editing.
- **US-10 / US-17 (Parking Facility & Downstream Operations):** Inspects live parking status, dynamically querying active allocations or reporting `NOT_PARKED`.
- **BAY Workspace Design System:** Delivers a native, accessible search interface (`SearchPage` and `VehicleSearchView`) embedded into the navigation shell.

---

## 2. API Endpoints & Contracts

### Endpoints

| Method | Route | Description | Authorization |
| :--- | :--- | :--- | :--- |
| **GET** | `/api/v1/vehicles/search/?plate=<str>` | Search vehicle and parking status via query parameter | `IsAuthenticated` (Admin, Operator, Customer [Own]) |
| **GET** | `/api/v1/vehicles/search/<str:plate>/` | Search vehicle and parking status via path parameter | `IsAuthenticated` (Admin, Operator, Customer [Own]) |
| **GET** | `/api/v1/vehicles/by-plate/<str:plate>/?include_status=true` | Enriched vehicle profile lookup with live parking status | `IsAuthenticated` (Admin, Operator, Customer [Own]) |

### Request Parameters
- `plate` (string, required): Normalized license plate (e.g. `KA-01-AB-1234`). Whitespace is automatically trimmed and characters are uppercased.

### Success Response (HTTP 200 OK)

```json
{
  "id": 10,
  "registration_number": "KA-01-MG-1000",
  "vehicle_type": "Compact",
  "owner": 4,
  "owner_username": "customer1",
  "owner_name": "Priya Sharma",
  "owner_phone": "9876543210",
  "created_at": "2026-10-24T18:00:00Z",
  "updated_at": "2026-10-24T18:30:00Z",
  "parking_status": {
    "is_parked": true,
    "status": "PARKED",
    "session_id": 205,
    "check_in_time": "2026-10-24T18:00:00Z",
    "slot": {
      "id": 14,
      "slot_number": "A-102",
      "zone": "North Wing",
      "floor": 1
    },
    "message": "Vehicle is currently parked in bay A-102."
  }
}
```

*When vehicle is not currently parked:*
```json
{
  "id": 10,
  "registration_number": "KA-01-MG-1000",
  "vehicle_type": "Compact",
  "owner": 4,
  "owner_username": "customer1",
  "owner_name": "Priya Sharma",
  "owner_phone": "9876543210",
  "created_at": "2026-10-24T18:00:00Z",
  "updated_at": "2026-10-24T18:30:00Z",
  "parking_status": {
    "is_parked": false,
    "status": "NOT_PARKED",
    "session_id": null,
    "check_in_time": null,
    "slot": null,
    "message": "Vehicle is not currently parked in any slot."
  }
}
```

### Error Responses

All handled DRF failures use the shared [US-31 error contract](US31-error-contract.md): `{error, code, details}`. Clients branch on the stable `code`, not message wording.

| Scenario | HTTP Status | Structured response |
| :--- | :--- | :--- |
| **Missing or invalid query** | `400 Bad Request` | `VALIDATION_ERROR`, with field-specific `details.plate` |
| **Unauthenticated request** | `401 Unauthorized` | `AUTHENTICATION_REQUIRED` |
| **Customer searches another owner's vehicle** | `403 Forbidden` | `PERMISSION_DENIED` |
| **Vehicle plate not found** | `404 Not Found` | `NOT_FOUND` |

Search intentionally accepts partial plate prefixes; complete registration-format validation is applied to registration and profile-update payloads, not search terms.

---

## 3. Role-Based Access Control (RBAC)

In compliance with SRS §8.2 and SAD §3.4.3:
- **Admin**: Full visibility. Permitted to search and inspect any vehicle across the facility.
- **Operator**: Operational visibility. Permitted to search and inspect any vehicle across the facility for gate management.
- **Customer**: Privacy-isolated visibility. Permitted to search and inspect vehicles owned by their authenticated account (`Permitted (Own)`). Unauthorized cross-user queries reject with HTTP 403 Forbidden.

---

## 4. Frontend Architecture & Design

- **`frontend/src/pages/Search.jsx`**: Page container for route compatibility.
- **`frontend/src/components/VehicleSearchView.jsx`**: Feature view implementing search bar, live status hero banner, automotive plate specification card, quick search shortcuts for user vehicles, and clear error/not-found states.
- **`frontend/src/components/AuthenticatedView.jsx`**: Integrated `search` tab into the BAY sidebar navigation with `BayIcon name="search"`.
- **`frontend/src/App.css`**: Defined `.vehicle-search-container`, `.search-bar-card`, `.live-status-hero`, `.status-parked`, `.status-not-parked`, and responsive breakpoints.

---

## 5. Automated Verification

- **Backend tests:** `backend/vehicles/tests/test_vehicle_search.py` (18 tests covering service normalization, parking status resolution, RBAC permissions, HTTP 400/401/403/404, and latency < 500ms).
- **Frontend tests:** `frontend/tests/vehicles.test.js` (60 tests covering client normalization, simulated API states, status badges, and navigation).
