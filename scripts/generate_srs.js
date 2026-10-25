const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun, Header, Footer,
  AlignmentType, PageOrientation, LevelFormat, HeadingLevel, BorderStyle, WidthType, ShadingType,
  PageNumber, PageBreak, TableOfContents, TabStopType, TabStopPosition, VerticalAlign
} = require('docx');

const FONT = 'Times New Roman';
const NAVY = '1F3864';
const GREY = 'F2F2F2';
const HEAD = 'D9E2F3';
const PW = 9026;           // portrait content width (A4, 1" margins)
const LW = 13958;          // landscape content width

// ---------- helpers ----------
const run = (t, o = {}) => new TextRun({ text: t, font: FONT, ...o });
function rich(text, base = {}) {
  // **bold** and _italic_ inline markup
  const out = [];
  const re = /(\*\*[^*]+\*\*|__[^_]+__)/g;
  let last = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(run(text.slice(last, m.index), base));
    const tok = m[0];
    if (tok.startsWith('**')) out.push(run(tok.slice(2, -2), { ...base, bold: true }));
    else out.push(run(tok.slice(2, -2), { ...base, italics: true }));
    last = m.index + tok.length;
  }
  if (last < text.length) out.push(run(text.slice(last), base));
  return out;
}
const P = (text, o = {}) => new Paragraph({
  spacing: { after: 120, line: 276 }, alignment: AlignmentType.JUSTIFIED,
  ...o.para, children: rich(text, o.run || {})
});
const H1 = t => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [run(t)], pageBreakBefore: false });
const H2 = t => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [run(t)] });
const H3 = t => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [run(t)] });
const B = (text, level = 0) => new Paragraph({
  numbering: { reference: 'bul', level }, spacing: { after: 60, line: 276 }, children: rich(text)
});
const cap = t => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 60, after: 200 },
  children: [run(t, { italics: true, size: 20 })] });
const tcap = t => new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 160, after: 80 },
  children: [run(t, { bold: true, size: 20 })] });
const pb = () => new Paragraph({ children: [new PageBreak()] });

const bd = { style: BorderStyle.SINGLE, size: 4, color: '808080' };
const borders = { top: bd, bottom: bd, left: bd, right: bd };
function cell(content, w, o = {}) {
  const paras = (Array.isArray(content) ? content : [content]).map(c =>
    (typeof c === 'string')
      ? new Paragraph({ spacing: { after: 40 }, alignment: o.align || AlignmentType.LEFT,
          children: rich(c, { size: o.size || 18, bold: o.bold, color: o.color }) })
      : c);
  return new TableCell({
    width: { size: w, type: WidthType.DXA }, borders,
    shading: o.fill ? { fill: o.fill, type: ShadingType.CLEAR, color: 'auto' } : undefined,
    margins: { top: 50, bottom: 50, left: 90, right: 90 }, verticalAlign: VerticalAlign.TOP, children: paras
  });
}
function table(headers, rows, widths, o = {}) {
  const total = widths.reduce((a, b) => a + b, 0);
  const hr = new TableRow({ tableHeader: true, cantSplit: true,
    children: headers.map((h, i) => cell(h, widths[i], { fill: HEAD, bold: true, size: o.size || 18 })) });
  const body = rows.map((r, ri) => new TableRow({ cantSplit: o.cantSplit !== false,
    children: r.map((c, i) => cell(c, widths[i], { size: o.size || 18, fill: (o.zebra && ri % 2) ? GREY : undefined })) }));
  return new Table({ width: { size: total, type: WidthType.DXA }, columnWidths: widths, rows: [hr, ...body] });
}
const gap = () => new Paragraph({ spacing: { after: 120 }, children: [] });

// ---------- requirement data ----------
// [id, statement, refinement|null, acceptance[], verification]
const FR = {
  // --- E1: Identity & Access Management (Member 1 / UC-01) ---
  'FR-15': [
    'The system shall securely authenticate users, issue JWT token pairs (access and refresh), and support secure logout.',
    'RTM refinement: covers user login, token-based session management, and invalidation upon logout.',
    [
      'Valid credentials return an access token and a refresh token (HTTP 200).',
      'Invalid credentials return HTTP 401 and no token is issued.',
      'An expired access token is rejected on protected endpoints.',
      'After logout, the invalidated token is rejected by protected endpoints.',
      'Token lifetimes and blacklist mechanism: TBD (UD-09). Role selection at registration: TBD (UD-13).'
    ],
    'T / TC-UC01-UNIT-001, TC-UC01-SYS-001'
  ],
  'FR-16': [
    'The system shall enforce Role-Based Access Control (RBAC) across Admin, Operator, and Customer roles.',
    'RTM refinement: ensures authorization checks on protected endpoints and client navigation.',
    [
      'A protected function is accessible only to roles explicitly permitted for it.',
      'Unauthorized or unauthenticated requests are rejected with HTTP 401 or HTTP 403 (NFR-SEC-01).',
      'Protected client routes and action buttons are conditionally rendered based on active role.',
      'Complete role-to-function permission matrix: TBD (UD-01, Section 9.2).'
    ],
    'T / TC-UC01-API-002'
  ],
  'FR-17': [
    'The system shall allow administrators to manage user accounts and user statuses (active, suspended, deactivated).',
    'RTM refinement: administrative control over user lifecycle and account access permissions.',
    [
      'An administrator can set a user account to active, suspended, or deactivated.',
      'Non-administrative attempts to modify user status return HTTP 403 (NFR-SEC-02).',
      'The updated status is persisted and enforced during authentication.',
      'Behavioural difference between suspended and deactivated accounts: TBD (UD-11).'
    ],
    'T / TC-UC04-API-001'
  ],
  'FR-18': [
    'The system shall allow users to inspect their profile, update personal contact details, and securely change passwords.',
    'RTM refinement: self-service user profile and password management.',
    [
      'A user can view their stored profile attributes and update personal contact details.',
      'Password changes require validation against strong password rules.',
      'New passwords are stored only in cryptographically hashed form (NFR-SEC-05).',
      'Password complexity rule set and current-password re-entry: TBD (UD-10).'
    ],
    'T / TC-UC04-API-002, TC-UC04-SYS-001'
  ],

  // --- E2: Vehicle Management (Member 1 / UC-02) ---
  'FR-01': [
    'The system shall allow an authorized user/operator to register a vehicle with plate number, vehicle type, and owner information.',
    'RTM refinement: initial vehicle entity creation and uniqueness enforcement.',
    [
      'A submission with plate number, vehicle type, and owner details creates a retrievable vehicle record.',
      'Missing or malformed mandatory fields are rejected with HTTP 400 (FR-13).',
      'Duplicate license plate registrations are rejected with an appropriate conflict error.',
      'Permitted vehicle types and owner profile fields: TBD (UD-15).'
    ],
    'T / TC-UC02-UNIT-001, TC-UC02-API-001'
  ],
  'FR-02': [
    'The system shall allow an authorized user/operator to view and update vehicle profile and registration details.',
    'RTM refinement: vehicle profile maintenance and contact update.',
    [
      'An authorized operator can view a stored vehicle record by ID or plate.',
      'A valid update is persisted and updates the last-modified timestamp.',
      'An invalid update payload is rejected and the stored record is unchanged.'
    ],
    'T / TC-UC02-API-002'
  ],
  'FR-11': [
    'The system shall allow authorized users/operators to search for a vehicle by license plate and inspect its current parking status.',
    'RTM refinement: quick vehicle lookup with active slot status.',
    [
      'Searching an existing license plate returns the vehicle and its current status (parked with slot, or not parked).',
      'A search with no match returns a structured not-found response (FR-14).',
      'Partial or fuzzy license plate matching: TBD.'
    ],
    'T / TC-UC02-API-001, TC-UC02-API-002'
  ],

  // --- E3: Parking Facility & Availability (Member 2 / UC-03) ---
  'FR-03': [
    'The system shall allow an authorized administrator/operator to add, modify, and deactivate parking slots and zones.',
    'RTM refinement: slot and zone lifecycle management.',
    [
      'An authorized user can create a slot with a unique identifier and assign it to a zone.',
      'An authorized user can modify slot properties or deactivate a slot/zone.',
      'Unauthorized attempts are rejected with HTTP 403 (NFR-SEC-01).',
      'Soft deactivation vs hard deletion semantics for historically referenced slots: TBD (UD-03).'
    ],
    'T / TC-UC03-UNIT-001'
  ],
  'FR-04': [
    'The system shall maintain the real-time status of each parking slot (Available, Occupied, Maintenance).',
    'RTM refinement: real-time state tracking across facility bays.',
    [
      'Each slot has exactly one status at any time.',
      'Check-in sets the status to Occupied; check-out releases the slot to Available.',
      'A slot in Maintenance or Occupied status cannot be assigned to arriving vehicles.',
      'Real-time refresh latency target: TBD (UD-17).'
    ],
    'T / TC-UC03-INT-001'
  ],
  'FR-07': [
    'The system shall prevent an occupied or unavailable parking slot from being assigned to another vehicle.',
    'RTM refinement: slot protection and allocation collision prevention.',
    [
      'A check-in attempt targeting an Occupied or Maintenance slot is rejected with an error.',
      'Slot status and existing parking records remain unaltered.'
    ],
    'T / TC-UC03-SYS-002, TC-UC05-INT-001'
  ],
  'FR-10': [
    'The system shall provide a live parking occupancy status dashboard for operators and users.',
    'RTM refinement: visual facility map and vacancy overview.',
    [
      'The dashboard shows slot identifiers, current states, and vehicle plate for occupied slots.',
      'The view dynamically reflects check-in, check-out, and status changes.',
      'Data scope and filter controls accessible to Customer role: TBD (UD-14).'
    ],
    'T, D / TC-UC03-SYS-002'
  ],

  // --- E4: Reservation Management (Member 2 / UC-04) ---
  'FR-19': [
    'The system shall allow authorized users to create advance parking reservations with scheduled time windows.',
    'RTM refinement: forward slot booking and scheduling.',
    [
      'A reservation submission with valid vehicle, slot, and future window creates a reservation record.',
      'Requests with past timestamps or invalid durations are rejected (FR-13).',
      'Maximum advance booking horizon: TBD.'
    ],
    'T / TC-UC04-API-001'
  ],
  'FR-20': [
    'The system shall prevent reservation slot conflicts and overlapping schedule commitments.',
    'RTM refinement: scheduling conflict protection for advance holds.',
    [
      'A reservation request for a slot already committed during an overlapping window is rejected.',
      'Zero double-booking overlap permitted across active reservations.'
    ],
    'T / TC-UC04-SYS-001'
  ],
  'FR-21': [
    'The system shall allow authorized users to modify or cancel an existing future reservation.',
    'RTM refinement: reservation lifecycle modification.',
    [
      'A user can cancel their confirmed future reservation prior to the cutoff threshold.',
      'A cancelled reservation releases the slot hold for subsequent booking.',
      'Cancellation window threshold and cancellation penalty fees: TBD.'
    ],
    'T / TC-UC04-API-001'
  ],
  'FR-22': [
    'The system shall link a valid reservation to vehicle check-in and automatically release unfulfilled reservations upon expiry.',
    'RTM refinement: reservation check-in claim and expiry cleanup.',
    [
      'An arriving vehicle with a confirmed reservation checks in seamlessly to the designated slot.',
      'An unfulfilled reservation exceeding the grace window is automatically expired and the slot released.',
      'Grace window duration before reservation forfeiture: TBD.'
    ],
    'T / TC-UC04-SYS-001'
  ],

  // --- E5: Parking Operations (Member 3 / UC-05, UC-06) ---
  'FR-05': [
    'The system shall allow an operator to check in a vehicle and allocate an available compatible parking slot.',
    'RTM refinement: check-in workflow and slot allocation.',
    [
      'Check-in of a vehicle with no active session to an available compatible slot creates an active record and sets the slot to Occupied.',
      'Check-in of an unregistered vehicle prompts registration or returns an error.',
      'Manual vs automated slot allocation selection: TBD (UD-04).'
    ],
    'T / TC-UC05-UNIT-001, TC-UC05-INT-001'
  ],
  'FR-06': [
    'The system shall enforce a single active parking session constraint per vehicle.',
    'RTM refinement: anti-passback and active session uniqueness.',
    [
      'Check-in for a vehicle with an existing active session is rejected with HTTP 409/400.',
      'No secondary parking record is created and no slot state changes.'
    ],
    'T / TC-UC05-INT-002'
  ],
  'FR-08': [
    'The system shall allow an operator to check out a vehicle upon request or exit verification.',
    'RTM refinement: checkout completion and timestamp recording.',
    [
      'Check-out of an active parking record records the check-out timestamp and marks the session completed.',
      'Check-out with no matching active record is rejected with an error.',
      'Exit verification mechanism (operator manual vs slip scan): TBD (UD-05).'
    ],
    'T / TC-UC06-INT-001'
  ],
  'FR-09': [
    'The system shall automatically release the corresponding parking slot to Available upon vehicle check-out.',
    'RTM refinement: automated slot state restoration.',
    [
      'Upon checkout completion, the associated slot status immediately returns to Available.',
      'The released slot is immediately eligible for new check-ins.'
    ],
    'T / TC-UC06-INT-002'
  ],
  'FR-12': [
    'The system shall maintain a persistent historical audit trail of completed parking sessions.',
    'RTM refinement: immutable parking history retention.',
    [
      'Completed records remain retrievable with vehicle, slot, check-in, check-out, and fee data.',
      'Check-out does not delete historical records.',
      'Historical retention duration and archiving policy: TBD (UD-12).'
    ],
    'T / TC-UC06-SYS-001'
  ],

  // --- E6: Pricing, Billing & Payment (Member 3 / UC-07, UC-08) ---
  'FR-23': [
    'The system shall allow administrators to configure parking tariff rates and pricing models by vehicle class.',
    'RTM refinement: tariff schedule and vehicle class rate administration.',
    [
      'An administrator can configure hourly rates, flat rates, and weekend multipliers by vehicle type.',
      'Tariff updates apply to all parking sessions initiated after configuration.',
      'Tariff schedule rates and vehicle classes: TBD (UD-07).'
    ],
    'T / TC-UC07-UNIT-001'
  ],
  'FR-24': [
    'The system shall automatically calculate parking session duration and compute applicable parking fees.',
    'RTM refinement: automated duration calculation and tariff evaluation.',
    [
      'Duration is calculated from check-in and check-out timestamps.',
      'Configured grace period is evaluated before assessing billing increments.',
      'Grace-period length and rounding increments: TBD (UD-06).'
    ],
    'T / TC-UC07-API-002'
  ],
  'FR-25': [
    'The system shall issue a digital parking slip, generate a QR token upon check-in, and provide payment receipts.',
    'RTM refinement: slip generation, QR token issuance, and receipt delivery.',
    [
      'Check-in generates a digital slip containing session ID, entry timestamp, and QR token.',
      'Check-out and payment produces a verifiable receipt.',
      'QR payload format and receipt layout: TBD (UD-08).'
    ],
    'T / TC-UC07-SYS-001'
  ],
  'FR-26': [
    'The system shall record payment transactions and track payment status across supported methods (Cash, Card, UPI).',
    'RTM refinement: multi-method payment recording and verification.',
    [
      'Payment transactions can be recorded as Cash, Card, or UPI with amount and timestamp.',
      'Successful payment marks the parking session as settled.',
      'External payment gateway integration vs operator recording: TBD (UD-07).'
    ],
    'T / TC-UC08-SYS-001'
  ],

  // --- E7: Admin Dashboard & Reporting (Member 4 / UC-08) ---
  'FR-27': [
    'The system shall provide an administrative dashboard displaying operational summary metrics.',
    'RTM refinement: real-time facility metrics aggregation.',
    [
      'Dashboard displays current occupancy rate, active session count, today revenue total, and available slots.',
      'Summary metrics update as check-in, checkout, and payments execute.'
    ],
    'T / TC-UC08-API-001'
  ],
  'FR-28': [
    'The system shall generate occupancy, usage, and revenue reports with configurable date-range filtering and export capabilities.',
    'RTM refinement: historical analytics, filtering, and CSV/PDF export.',
    [
      'Reports aggregate entry counts, peak hours, and revenue over chosen date ranges.',
      'Export functions produce valid CSV and PDF report files.',
      'Report aggregation intervals and export layout schemas: TBD (UD-14).'
    ],
    'T / TC-UC08-API-002, TC-UC08-SYS-001'
  ],

  // --- E8: Audit, Notifications & Quality (Member 4 / UC-09, UC-10) ---
  'FR-29': [
    'The system shall maintain a persistent audit log recording security events, administrative changes, and critical domain operations.',
    'RTM refinement: immutable system audit logging.',
    [
      'Audit entries capture event category, user ID, timestamp, and action parameters.',
      'Audit log records cannot be modified or deleted via application endpoints.',
      'Audit event classification and retention schedule: TBD (UD-12).'
    ],
    'T / TC-UC09-INT-001, TC-UC09-SYS-001'
  ],
  'FR-30': [
    'The system shall deliver in-app notifications for key parking and reservation lifecycle milestones.',
    'RTM refinement: milestone notification alerts.',
    [
      'Notifications are issued for reservation creation, upcoming expiry, and payment completion.',
      'Users can view notification history within the client interface.'
    ],
    'T / TC-UC09-SYS-002'
  ],
  'FR-13': [
    'The system shall validate all client-submitted input data on the server side before processing.',
    'RTM refinement: universal server-side payload validation.',
    [
      'Missing, malformed, or invalid fields are rejected before database commit.',
      'Rejection returns HTTP 400 with structured validation details (NFR-SEC-03).',
      'Validation applies across all API endpoints.'
    ],
    'T / TC-UC10-API-001'
  ],
  'FR-14': [
    'The system shall return uniform structured error responses and standard HTTP status codes.',
    'RTM refinement: standardized error envelope and response schema.',
    [
      'Every failure returns a structured JSON payload ({error, code, details}) and standard HTTP code.',
      'User interface renders human-readable feedback from response payload.',
      'Standard error code enum mapping: TBD (Section 10).'
    ],
    'T / TC-UC10-API-001'
  ]
};


function frTable(ids) {
  const W = [850, 3300, 3876, 1000];
  const rows = ids.map(id => {
    const [st, ref, ac, ver] = FR[id];
    const reqCell = [`**${id}:** ${st}`];
    if (ref) reqCell.push(`__${ref}__`);
    return [`**${id}**`, reqCell, ac.map((a, i) => `(${String.fromCharCode(97 + i)}) ${a}`), ver];
  });
  return table(['ID', 'Requirement', 'Acceptance Criteria', 'Verification'], rows, W, { size: 17 });
}

// ---------- RTM data ----------
const RTM = [
  ['FR-01','Register vehicle with plate number, vehicle type, and owner information','US-05 (#25)','Vehicle Management','Member 1','docs/SAD/Vehicle_Parking_System_SAD.md §3.4.3 Vehicle Management','backend/vehicles/models.py; frontend/src/pages/Vehicles.jsx','TC-UC02-UNIT-001; TC-UC02-API-001'],
  ['FR-02','View and update vehicle profile and registration details','US-06 (#26)','Vehicle Management','Member 1','docs/SAD/Vehicle_Parking_System_SAD.md §3.4.3 Vehicle Management','backend/vehicles/views.py; frontend/src/pages/Vehicles.jsx','TC-UC02-API-002'],
  ['FR-03','Add, modify, and deactivate parking slots and zones','US-09 (#29)','Parking Facility & Availability','Member 2','docs/SAD/Vehicle_Parking_System_SAD.md §3.4.4 Slot Allocation Engine','backend/slots/models.py; frontend/src/pages/Slots.jsx','TC-UC03-UNIT-001'],
  ['FR-04','Maintain real-time slot state (Available, Occupied, Maintenance)','US-10 (#30)','Parking Facility & Availability','Member 2','docs/SAD/Vehicle_Parking_System_SAD.md §3.4.4 Slot Allocation Engine','backend/slots/services.py','TC-UC03-INT-001'],
  ['FR-05','Check-in vehicle and allocate an available compatible parking slot','US-17 (#37)','Parking Operations','Member 3','docs/SAD/Vehicle_Parking_System_SAD.md §3.4.5 Parking Operations','backend/operations/views.py','TC-UC05-UNIT-001; TC-UC05-INT-001'],
  ['FR-06','Enforce single-active-session constraint per vehicle','US-18 (#38)','Parking Operations','Member 3','docs/SAD/Vehicle_Parking_System_SAD.md §3.4.5 Parking Operations','backend/operations/services.py','TC-UC05-INT-002'],
  ['FR-07','Prevent assignment to occupied or unavailable parking slot','US-12 (#32); US-17 (#37)','Parking Facility / Operations','Member 4 (Reassigned from Member 2) / Member 3','docs/SAD/Vehicle_Parking_System_SAD.md §3.4.4, §3.4.5','backend/operations/services.py','TC-UC03-SYS-002; TC-UC05-INT-001'],
  ['FR-08','Check-out vehicle upon operator request or exit verification','US-19 (#39)','Parking Operations','Member 3','docs/SAD/Vehicle_Parking_System_SAD.md §3.4.5 Parking Operations','backend/operations/views.py','TC-UC06-INT-001'],
  ['FR-09','Automatically release parking slot to Available upon checkout','US-19 (#39)','Parking Operations','Member 3','docs/SAD/Vehicle_Parking_System_SAD.md §3.4.5 Parking Operations','backend/operations/services.py','TC-UC06-INT-002'],
  ['FR-10','Live parking occupancy status dashboard for operators and users','US-11 (#31)','Parking Facility & Availability','Member 4 (Reassigned from Member 2)','docs/SAD/Vehicle_Parking_System_SAD.md §3.4.4 Slot Allocation Engine','frontend/src/pages/Dashboard.jsx','TC-UC03-SYS-002'],
  ['FR-11','Search vehicle by license plate and inspect current parking status','US-07 (#27)','Vehicle Management','Member 1','docs/SAD/Vehicle_Parking_System_SAD.md §3.4.3 Vehicle Management','backend/vehicles/views.py; frontend/src/pages/Search.jsx','TC-UC02-API-001; TC-UC02-API-002'],
  ['FR-12','Maintain persistent historical audit trail of parking sessions','US-20 (#40)','Parking Operations','Member 3','docs/SAD/Vehicle_Parking_System_SAD.md §3.4.5 Parking Operations','backend/operations/models.py; frontend/src/pages/History.jsx','TC-UC06-SYS-001'],
  ['FR-13','Backend data validation for all client-submitted payload fields','US-08 (#28); US-31 (#51)','Validation & Common','Member 1 / Member 4','docs/SAD/Vehicle_Parking_System_SAD.md §3.4.9, §4.5 Validation','backend/common/serializers.py','TC-UC10-API-001'],
  ['FR-14','Uniform structured error messaging and standard HTTP error codes','US-08 (#28); US-31 (#51)','Validation & Common','Member 1 / Member 4','docs/SAD/Vehicle_Parking_System_SAD.md §3.4.9, §4.5 Validation','backend/common/exceptions.py','TC-UC10-API-001'],
  ['FR-15','User authentication, token issuance, and secure logout','US-01 (#1)','Identity & Access Management','Member 1','docs/SAD/Vehicle_Parking_System_SAD.md §3.4.2 Auth, §3.9 Security','backend/accounts/views.py; frontend/src/context/AuthContext.jsx','TC-UC01-UNIT-001; TC-UC01-SYS-001'],
  ['FR-16','Role-Based Access Control enforcement (Admin, Operator, Customer)','US-02 (#22)','Identity & Access Management','Member 1','docs/SAD/Vehicle_Parking_System_SAD.md §3.4.2 Auth, §3.9 Security','backend/accounts/permissions.py; frontend/src/routes/ProtectedRoute.jsx','TC-UC01-API-002'],
  ['FR-17','Administrative management of user status (active, suspended, deactivated)','US-03 (#23)','Identity & Access Management','Member 1','docs/SAD/Vehicle_Parking_System_SAD.md §3.4.2 Auth, §3.9 Security','backend/accounts/views.py','TC-UC04-API-001'],
  ['FR-18','User profile inspection, contact details update, and password change','US-04 (#24)','Identity & Access Management','Member 1','docs/SAD/Vehicle_Parking_System_SAD.md §3.4.2 Auth, §3.9 Security','backend/accounts/serializers.py; frontend/src/pages/Profile.jsx','TC-UC04-API-002; TC-UC04-SYS-001'],
  ['FR-19','Advance parking reservation creation and scheduling','US-13 (#33)','Reservation Management','Member 2','docs/SAD/Vehicle_Parking_System_SAD.md §3.4.7 Reservation Module','backend/reservations/models.py; frontend/src/pages/Reservations.jsx','TC-UC04-API-001'],
  ['FR-20','Prevent reservation conflicts and overlapping slot commitments','US-15 (#35)','Reservation Management','Member 2','docs/SAD/Vehicle_Parking_System_SAD.md §3.4.7 Reservation Module','backend/reservations/services.py','TC-UC04-SYS-001'],
  ['FR-21','Modify or cancel an existing future reservation','US-14 (#34)','Reservation Management','Member 2','docs/SAD/Vehicle_Parking_System_SAD.md §3.4.7 Reservation Module','backend/reservations/views.py','TC-UC04-API-001'],
  ['FR-22','Link valid reservation to check-in session and release upon expiry','US-16 (#36)','Reservation Management','Member 2','docs/SAD/Vehicle_Parking_System_SAD.md §3.4.7 Reservation Module','backend/reservations/services.py','TC-UC04-SYS-001'],
  ['FR-23','Configure vehicle-class rates and parking tariff models','US-21 (#41)','Pricing, Billing & Payment','Member 3','docs/SAD/Vehicle_Parking_System_SAD.md §3.4.6 Billing & Pricing','backend/billing/models.py','TC-UC07-UNIT-001'],
  ['FR-24','Automatic duration calculation and parking fee computation','US-22 (#42)','Pricing, Billing & Payment','Member 3','docs/SAD/Vehicle_Parking_System_SAD.md §3.4.6 Billing & Pricing','backend/billing/services.py','TC-UC07-API-002'],
  ['FR-25','Digital parking slip issuance, QR token generation, and receipts','US-23 (#43)','Pricing, Billing & Payment','Member 3','docs/SAD/Vehicle_Parking_System_SAD.md §3.4.6 Billing & Pricing','backend/billing/services.py','TC-UC07-SYS-001'],
  ['FR-26','Record payment transaction status (Cash, Card, UPI)','US-24 (#44)','Pricing, Billing & Payment','Member 3','docs/SAD/Vehicle_Parking_System_SAD.md §3.4.6 Billing & Pricing','backend/billing/views.py','TC-UC08-SYS-001'],
  ['FR-27','Administrative dashboard summary metrics (occupancy, active sessions)','US-25 (#45)','Admin Dashboard & Reporting','Member 4','docs/SAD/Vehicle_Parking_System_SAD.md §3.4.8 Reporting & Analytics','frontend/src/pages/AdminDashboard.jsx','TC-UC08-API-001'],
  ['FR-28','Occupancy, parking usage, and revenue reporting with date filters','US-26 (#46); US-27 (#47); US-28 (#48)','Admin Dashboard & Reporting','Member 4','docs/SAD/Vehicle_Parking_System_SAD.md §3.4.8 Reporting & Analytics','backend/reports/views.py; frontend/src/pages/Reports.jsx','TC-UC08-API-002; TC-UC08-SYS-001'],
  ['FR-29','Persistent system audit log tracking security and domain events','US-29 (#49)','Audit, Notifications & Quality','Member 4','docs/SAD/Vehicle_Parking_System_SAD.md §3.4.9 Audit & Notifications','backend/common/models.py','TC-UC09-INT-001; TC-UC09-SYS-001'],
  ['FR-30','In-app notification delivery for parking and reservation milestones','US-30 (#50)','Audit, Notifications & Quality','Member 4','docs/SAD/Vehicle_Parking_System_SAD.md §3.4.9 Audit & Notifications','backend/notifications/models.py; frontend/src/components/Notifications.jsx','TC-UC09-SYS-002'],
];
const NFR = [
  ['NFR-PERF-01','Performance','API interactive response time under standard load','Automated API benchmark tests','< 500 ms p95 response time for CRUD endpoints'],
  ['NFR-PERF-02','Concurrency','Concurrent check-in/out consistency without race conditions','Database transactions and isolation tests','ACID transactional consistency under 50+ concurrent requests'],
  ['NFR-PERF-03','Scalability','Search and history indexing remains responsive under growth','Indexed queries on license plate and timestamps','< 200 ms query time on 100,000 records'],
  ['NFR-SAFE-01','Safety','Prevent multi-vehicle assignment to a single slot','Unique database constraints and model validations','0 double-allocation violations'],
  ['NFR-SAFE-02','Safety','Prevent vehicle assignment to multiple active slots','Active session uniqueness validation','0 duplicate active sessions'],
  ['NFR-SAFE-03','Safety','Atomic transaction rollback on partial check-in/out failure','transaction.atomic blocks in Django service layer','Zero partial or corrupted records on error'],
  ['NFR-SEC-01','Security','Role-based permission enforcement on protected routes','DRF permission class tests and frontend router tests','100% unauthorized requests return HTTP 401/403'],
  ['NFR-SEC-02','Security','Prevent privilege escalation by non-admin roles','Unit tests for admin-only endpoint protection','0 unauthorized administrative actions'],
  ['NFR-SEC-03','Security','Strict server-side payload validation','DRF serializer validation tests','Rejection of malformed input with HTTP 400'],
  ['NFR-SEC-04','Security','Transport Layer Security (HTTPS) and secure CORS origin policy','CI/CD configuration check and CORS whitelist','Restricted to trusted client origins'],
  ['NFR-SEC-05','Security','Cryptographic password hashing (Argon2 / PBKDF2) and JWT expiry','Django password validation settings and token unit tests','Zero plain-text credentials stored or transmitted'],
];

// ---------- front matter & images ----------
const img1Path = path.resolve(__dirname, 'word/media/image1.png');
const img2Path = path.resolve(__dirname, 'word/media/image2.png');
let img1 = null;
let img2 = null;

if (fs.existsSync(img1Path)) {
  try {
    img1 = fs.readFileSync(img1Path);
  } catch (err) {
    console.warn('Warning: Could not read image1.png:', err.message);
  }
}
if (fs.existsSync(img2Path)) {
  try {
    img2 = fs.readFileSync(img2Path);
  } catch (err) {
    console.warn('Warning: Could not read image2.png:', err.message);
  }
}

const cover = [
  new Paragraph({ spacing: { before: 1000 }, alignment: AlignmentType.CENTER, children: [run('PES UNIVERSITY, BANGALORE', { bold: true, size: 26 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 1200 }, children: [run('Department of Computer Science and Engineering', { size: 24 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: [run('SOFTWARE REQUIREMENTS SPECIFICATION', { bold: true, size: 40, color: NAVY })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: [run('for', { italics: true, size: 24 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 300 }, border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: NAVY, space: 12 } },
    children: [run('VEHICLE PARKING SYSTEM', { bold: true, size: 48, color: NAVY })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 300, after: 800 }, children: [run('Version 1.1 (Consolidated & Expanded Specification)', { bold: true, size: 26 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, children: [run('Prepared and Edited by (Lead Editor):', { italics: true, size: 22 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 100 }, children: [run('Trisha Vallamkonda Prathap (Member 1)', { bold: true, size: 28, color: NAVY })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 400 }, children: [run('Scrum Master & Project Integration Lead', { size: 22, italics: true })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, children: [run('Original Baseline SRS (v1.0) Author:', { italics: true, size: 20 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 600 }, children: [run('Vishwas Gowda S (Member 4)', { bold: true, size: 22 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, children: [run('Course: UE24CS341A Software Engineering (Mini-Project)', { size: 22 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, children: [run('Repository: Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT', { size: 20 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 400 }, children: [run('12 October 2026', { size: 24 })] }),
];

const revision = [
  new Paragraph({ heading: HeadingLevel.HEADING_1, children: [run('Revision History')] }),
  table(['Version', 'Date', 'Author / Editor', 'Reason for Changes'], [
    ['1.0', '01 Oct 2026', 'Vishwas Gowda S (Member 4)', 'Initial baseline requirements specification (FR-01 to FR-14; preliminary NFRs).'],
    ['1.1', '12 Oct 2026', 'Trisha Vallamkonda Prathap (Member 1)', 'Consolidated & Expanded SRS (Lead Editor): Expands and revises the v1.0 baseline. Incorporated full agreed scope FR-15 to FR-30 (Identity & Access Management, advanced slot management, check-in/out ticketing, tariff calculation, and analytics reporting), synchronized with RTM v1.0.0, added formal acceptance criteria, data definitions, uniform error handling, verification criteria, and unresolved decision (TBD) register.'],
    ['1.1.1', '25 Oct 2026', 'Trisha Vallamkonda Prathap (Member 1)', 'Workload Balancing & Story Reassignment: Documented transfer of unfinished stories US-11 (#31, FR-10) and US-12 (#32, FR-07) from Member 2 to Member 4 due to Member 2 availability constraints. Member 2 retains completed stories US-09, US-10 and Epic E4 (US-13..16); Member 4 assumes US-11 and US-12 in addition to Epics E7 and E8.'],
  ], [1000, 1400, 2200, 4426]),
  gap(),
  new Paragraph({ children: [run('Source baseline: ', { bold: true, size: 20 }), run('Vehicle_Parking_System_SRS.docx (v1.0 authored by Vishwas Gowda S) and Requirements Traceability Matrix v1.0.0 (prepared by Trisha Vallamkonda Prathap, October 2026).', { size: 20 })] }),
];

const toc = [
  new Paragraph({ children: [new PageBreak()] }),
  new Paragraph({ children: [run('Table of Contents', { bold: true, size: 32, color: NAVY })], spacing: { after: 200 } }),
  new TableOfContents('Table of Contents', { hyperlink: true, headingStyleRange: '1-3' }),
];

// ---------- body ----------
const body = [];
const add = (...x) => body.push(...x);

// 1 Introduction
add(H1('1. Introduction'),
  H2('1.1 Purpose'),
  P('This Software Requirements Specification (SRS) defines the functional and non-functional requirements of Version 1.0 of the Vehicle Parking System. It covers account and access management, vehicle registration and search, parking-slot and zone management, vehicle check-in and check-out, billing and payments, reporting, and cross-cutting validation and error handling. The document is organized after the IEEE SRS structure used in the course template and is the baseline for design, implementation, and verification.'),
  H2('1.2 Intended Audience and Reading Suggestions'),
  P('This document is intended for developers, testers, project team members, evaluators, and other stakeholders. General readers should read Sections 1 and 2. Developers and testers should read Sections 3 to 13 and Appendix B. Evaluators may use Section 12 and Appendix B to check traceability.'),
  H2('1.3 Product Scope'),
  P('The Vehicle Parking System is a web-based application for managing vehicle entry and exit, parking-slot allocation and status, user access, fee computation, payments, and parking reports. In scope:'),
  B('Account registration, JWT-based authentication, logout, role-based access control, profile and password management, user-status administration, and security audit trail (Section 5.1).'),
  B('Vehicle registration, update, search by license plate, and persistent parking history (Section 5.2).'),
  B('Parking-slot and zone administration, slot status, slot classification and vehicle-type constraints, and the live occupancy dashboard (Section 5.3).'),
  B('Check-in with compatible slot assignment, single-active-session enforcement, check-out, slot release, digital slip/QR token, and duration and grace-period calculation (Section 5.4).'),
  B('Tariff computation, payment processing and receipts, summary reports, and CSV/PDF export (Section 5.5).'),
  B('Input validation and uniform structured error handling (Section 5.6).'),
  P('Hardware integration (for example gate barriers or QR/exit scanners) is not specified in the source documents and is therefore not part of this baseline; see UD-05 and UD-08.'),
  H2('1.4 Definitions, Acronyms, and Abbreviations'),
  P('Terms are defined in Appendix A.'),
  H2('1.5 Document Conventions'),
  B('**shall** denotes a mandatory requirement. **TBD** denotes information not specified in the source documents; each TBD is referenced to a decision in Section 13.'),
  B('Functional requirements use the IDs FR-01 to FR-30, identical to the Requirements Traceability Matrix (RTM). FR-01 to FR-14 retain their v1.0 wording; FR-15 to FR-30 are taken from the RTM. RTM refinements of FR-01 to FR-14 appear as italic notes and do not replace the v1.0 statement.'),
  B('Non-functional requirements use NFR-PERF-nn, NFR-SAFE-nn, and NFR-SEC-nn; business rules use BR-nn; unresolved decisions use UD-nn; user stories use US-xx-nn; test cases use TC-xx-nn.'),
  B('Verification methods: **T** = Test, **I** = Inspection, **D** = Demonstration, **A** = Analysis.'),
  H2('1.6 References'),
  B('PES University, UE24CS341A Software Engineering, Jackfruit Mini-Project Guidelines 2026, Phase-1 SRS template.'),
  B('Vehicle Parking System SRS, Version 1.0, 01 October 2026.'),
  B('Vehicle Parking System Requirements Traceability Matrix, Version 1.0.0, October 2026.'),
  B('IEEE Std 830-1998 and ISO/IEC/IEEE 29148:2018, requirements specification practice.'),
  B('Django, Django REST Framework, React, and PostgreSQL documentation.'),
);

// 2 Overall description
add(H1('2. Overall Description'),
  H2('2.1 Product Perspective'),
  P('The Vehicle Parking System is a new, self-contained web application with three logical layers.'),
  table(['Layer', 'Technology / Responsibility'], [
    ['Presentation', 'React: browser-based user interface and protected client routes.'],
    ['Application / API', 'Django and Django REST Framework: business logic, validation, authentication, authorization, and REST endpoints.'],
    ['Persistence', 'PostgreSQL: users, vehicles, slots, zones, parking records and history, tickets, tariffs, invoices, and audit records.'],
  ], [2200, 6826]),
  gap(),
  H2('2.2 Product Functions'),
  table(['Epic / Module', 'Summary of Responsibilities', 'Requirements', 'Owner'], [
    ['E1: Identity & Access Management', 'Registration, JWT authentication, logout, RBAC, profile, password change, user status administration.', 'FR-15, FR-16, FR-17, FR-18', 'Member 1'],
    ['E2: Vehicle Management', 'Vehicle registration, profile updates, license plate lookup, and active status search.', 'FR-01, FR-02, FR-11', 'Member 1'],
    ['E3: Parking Facility & Availability', 'Bay and zone lifecycle, real-time availability states, bay protection, live occupancy dashboard.', 'FR-03, FR-04, FR-07, FR-10', 'Member 2 (US-09, US-10) / Member 4 (US-11, US-12)'],
    ['E4: Reservation Management', 'Advance booking scheduling, conflict prevention, reservation modification/cancellation, and hold expiry.', 'FR-19, FR-20, FR-21, FR-22', 'Member 2'],
    ['E5: Parking Operations', 'Vehicle check-in, bay allocation, anti-passback enforcement, check-out, bay release, persistent history.', 'FR-05, FR-06, FR-08, FR-09, FR-12', 'Member 3'],
    ['E6: Pricing, Billing & Payment', 'Tariff configuration, automated duration/fee calculation, digital slip/QR token, payment recording.', 'FR-23, FR-24, FR-25, FR-26', 'Member 3'],
    ['E7: Admin Dashboard & Reporting', 'Executive summary metrics, occupancy analytics, revenue reports, filterable CSV and PDF exports.', 'FR-27, FR-28', 'Member 4'],
    ['E8: Audit, Notifications & System', 'Immutable security audit trail, milestone notifications, payload validation, structured error responses.', 'FR-29, FR-30, FR-13, FR-14', 'Member 4 / Team'],
  ], [2600, 3226, 2100, 1100]),
  gap(),
  H2('2.3 User Classes and Characteristics'),
  table(['User Class', 'Primary Responsibilities', 'Access Characteristics'], [
    ['Administrator (Admin)', 'Administers slots and zones, manages user status, and views system parking information and reports.', 'Privileged authorized user.'],
    ['Operator', 'Registers and updates vehicles, performs check-in and check-out, manages slots where permitted, searches, and views status and history.', 'Operational authorized user.'],
    ['Customer', 'Registers/views vehicles where permitted, views status, and searches vehicles. Called "Authorized User" in SRS v1.0 (UD-01).', 'Authenticated user with role-limited access.'],
  ], [2000, 4626, 2400]),
  gap(),
  H2('2.4 Operating Environment'),
  B('Client: modern web browser running the React application; supported browser/version matrix is TBD (UD-17).'),
  B('Backend: Python environment with Django and Django REST Framework.'),
  B('Database: PostgreSQL relational database.'),
  B('Deployment host operating system, production versions, and hosting platform: TBD (UD-17).'),
  H2('2.5 Design and Implementation Constraints'),
  B('The backend shall use Django with Django REST Framework; the client shall use React; persistent data shall be stored in PostgreSQL.'),
  B('Frontend and backend shall interact through REST-style APIs with JWT-based authentication (FR-16).'),
  B('The design shall keep an active parking assignment consistent with the slot status (NFR-SAFE-03).'),
  B('Role restrictions shall follow the Admin, Operator, and Customer responsibilities (FR-18).'),
  H2('2.6 Assumptions and Dependencies'),
  B('Users of protected functions are authenticated and hold exactly one role.'),
  B('Each vehicle is uniquely identified by its registration (license plate) number.'),
  B('Each parking slot has a unique identifier and exactly one current status.'),
  B('Network connectivity exists between browser and backend, and the PostgreSQL service is available.'),
  B('Payment methods Cash, Card, and UPI are in scope (FR-28); any external payment provider is TBD (UD-07).'),
  B('Production capacity targets beyond those in Section 8 and the deployment platform are TBD (UD-17).'),
);

// 3 Interfaces
add(H1('3. External Interface Requirements'),
  H2('3.1 User Interfaces'),
  P('The system shall provide a browser-based graphical interface that presents functions according to the user role and gives feedback for successful and unsuccessful operations (FR-14, FR-18). Layout, branding, and detailed screen design are design-phase concerns.'),
  table(['Interface / View', 'Purpose', 'Related Requirements'], [
    ['Registration / Login / Logout', 'Create an account, authenticate, and end a session.', 'FR-15, FR-16, FR-17'],
    ['Profile and Password', 'View/update contact details and change password.', 'FR-19, FR-20'],
    ['User Administration', 'Set user status to active, suspended, or deactivated.', 'FR-21'],
    ['Vehicle Registration / Edit', 'Capture and maintain vehicle information.', 'FR-01, FR-02'],
    ['Vehicle Search / History', 'Search by license plate; show current status and previous parking records.', 'FR-11, FR-12'],
    ['Parking Slot and Zone Management', 'Add, modify, deactivate, and classify slots and zones.', 'FR-03, FR-23, FR-24'],
    ['Occupancy Dashboard', 'Show current slot states and occupancy.', 'FR-04, FR-10'],
    ['Vehicle Check-In', 'Select/register a vehicle, assign a compatible available slot, and issue a ticket/QR token.', 'FR-05 to FR-07, FR-25'],
    ['Vehicle Check-Out and Payment', 'Locate the active record, complete checkout, show duration and fee, record payment, issue receipt.', 'FR-08, FR-09, FR-26 to FR-28'],
    ['Reports and Export', 'View summary reports and export logs and analytics.', 'FR-29, FR-30'],
  ], [2500, 4426, 2100]),
  gap(),
  H2('3.2 Software Interfaces'),
  table(['Component', 'Interface', 'Data Exchanged', 'Purpose'], [
    ['React frontend', 'REST API (Django REST Framework)', 'JSON requests/responses; JWT access token', 'Submit commands; retrieve vehicles, slots, status, history, billing and reports.'],
    ['Django / DRF backend', 'PostgreSQL', 'Structured relational records', 'Persist data and enforce transactional consistency.'],
    ['Django / DRF backend', 'Application services and validation', 'Validated domain objects and errors', 'Apply business rules, role checks, and input validation.'],
    ['Payment channel (Card, UPI)', 'TBD', 'TBD', 'Process payments (FR-28); provider and interface TBD (UD-07).'],
  ], [2000, 2300, 2300, 2426]),
  gap(),
  H2('3.3 Communications Interfaces'),
  B('The frontend and backend shall communicate over HTTP/HTTPS; production traffic shall use HTTPS and a restricted CORS origin policy (NFR-SEC-04).'),
  B('API payloads shall use JSON; exports use CSV and PDF files (FR-30).'),
  B('Hostname, ports, network topology, and API versioning scheme: TBD (UD-17).'),
  H2('3.4 Hardware Interfaces'),
  P('No hardware interface is specified. Devices for reading QR tokens (FR-25) and for exit verification (FR-08) are TBD (UD-05, UD-08).'),
);

// 4 Analysis models
const useCasePara = img1
  ? new Paragraph({ alignment: AlignmentType.CENTER, children: [new ImageRun({ type: 'png', data: img1, transformation: { width: 300, height: 514 }, altText: { title: 'Use case model', description: 'Use case diagram', name: 'usecase' } })] })
  : new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 120 }, children: [run('[Placeholder: Use Case Model Diagram - image1.png not available]', { italics: true, color: '808080' })] });

const erPara = img2
  ? new Paragraph({ alignment: AlignmentType.CENTER, children: [new ImageRun({ type: 'png', data: img2, transformation: { width: 520, height: 173 }, altText: { title: 'ER model', description: 'Conceptual entity relationship diagram', name: 'er' } })] })
  : new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 120 }, children: [run('[Placeholder: Conceptual ER Model Diagram - image2.png not available]', { italics: true, color: '808080' })] });

add(H1('4. Analysis Models'),
  P('The models below are requirements-level models from the baseline and are subject to refinement in the design phase.'),
  H2('4.1 Use Case Model'),
  useCasePara,
  cap('Figure 1. Requirements-level use case model (baseline scope of SRS v1.0).'),
  P('Figure 1 illustrates the initial baseline use cases carried over from SRS v1.0. **Status Flag: Preliminary / Non-Final Baseline Diagram.** As tracked in UD-16, this legacy diagram represents only the initial scope (FR-01 to FR-14) and does not yet diagrammatically illustrate the expanded modules introduced in Version 1.1 (FR-15 to FR-30), including Identity & Access Management (registration, JWT authentication, RBAC), QR ticketing, tariffs, and reporting. The comprehensive use-case diagram reflecting the complete 30 requirements will be delivered during the detailed design phase.'),
  H2('4.2 Conceptual Entity-Relationship Model'),
  erPara,
  cap('Figure 2. Conceptual data model (baseline scope of SRS v1.0).'),
  P('Figure 2 illustrates the conceptual data model from SRS v1.0. **Status Flag: Preliminary / Non-Final Baseline Diagram.** It depicts the core legacy entities (User, Vehicle, ParkingSlot, ParkingRecord). The expanded entities introduced in Version 1.1 (CustomUser, Profile, AuditLog, Zone, SlotType, Ticket, Tariff, Invoice) are formally defined in Section 4.3 below and will be incorporated into the comprehensive ER model during the design phase (UD-16).'),
  H2('4.3 Conceptual Entity Summary'),
  P('Entity names are the model references used in the RTM design column.'),
  table(['Entity', 'Purpose', 'Requirements'], [
    ['CustomUser', 'User account with credentials, role, and status.', 'FR-15, FR-16, FR-18, FR-21'],
    ['Profile', 'Personal contact details of a user.', 'FR-19'],
    ['AuditLog', 'Authentication events and security changes.', 'FR-22'],
    ['Vehicle', 'Registered vehicle: plate number, type, owner information.', 'FR-01, FR-02, FR-11'],
    ['ParkingSlot', 'Parking slot with status and classification.', 'FR-03, FR-04, FR-10'],
    ['Zone', 'Grouping of slots by zone, floor, and section.', 'FR-03, FR-23'],
    ['SlotType', 'Slot vehicle-type constraint (Two-Wheeler, Compact, SUV, EV Charging).', 'FR-24'],
    ['ParkingRecord', 'Active or completed parking session of a vehicle in a slot.', 'FR-05 to FR-09, FR-26'],
    ['ParkingHistory', 'Retained history of completed sessions.', 'FR-12'],
    ['Ticket', 'Digital parking slip / QR token issued at check-in.', 'FR-25'],
    ['Tariff', 'Fee rules (flat-rate and dynamic) by vehicle class.', 'FR-27'],
    ['Invoice', 'Fee and payment for a session, with receipt.', 'FR-28'],
  ], [1800, 5026, 2200]),
  gap(),
);

// 5 Functional requirements
add(H1('5. Functional Requirements'),
  P('Functional requirements FR-01 to FR-30 are organized below across the 8 agreed project Epics (E1 to E8), corresponding to Use Cases UC-01 through UC-10 defined in the Software Test Plan. Verification strategies align with the agile traceability baseline.'),

  H2('5.1 Identity and Access Management (Epic E1 / UC-01)'),
  H3('5.1.1 Description and Priority'),
  P('Provides user registration, secure JWT authentication (access and refresh token pair), secure logout, role-based access control, profile inspection, password change, administrative user-status management, and security audit records. Owner: Member 1. Priority: High.'),
  H3('5.1.2 Stimulus/Response Sequences'),
  B('A user submits credentials; the system returns access and refresh JWT tokens or rejects the attempt with HTTP 401.'),
  B('A user requests logout; the system invalidates tokens and terminates the active session.'),
  B('A request reaches a protected route; the system validates role permissions and allows access or returns HTTP 403.'),
  B('An administrator updates a user status; the system persists the change and records an audit trail entry.'),
  H3('5.1.3 Functional Requirements'),
  tcap('Table 5-1. Identity and Access Management Requirements (Epic E1)'),
  frTable(['FR-15','FR-16','FR-17','FR-18']),
  gap(),

  H2('5.2 Vehicle Management (Epic E2 / UC-02)'),
  H3('5.2.1 Description and Priority'),
  P('Provides vehicle registration, profile updates, license plate lookup, and parking status inspection. Owner: Member 1. Priority: High.'),
  H3('5.2.2 Stimulus/Response Sequences'),
  B('An authorized user submits vehicle registration data; the system validates fields and stores the vehicle record.'),
  B('An operator searches by license plate; the system returns vehicle profile and active parking status.'),
  B('An authorized user updates vehicle details; the system validates and updates the record.'),
  H3('5.2.3 Functional Requirements'),
  tcap('Table 5-2. Vehicle Management Requirements (Epic E2)'),
  frTable(['FR-01','FR-02','FR-11']),
  gap(),

  H2('5.3 Parking Facility & Availability (Epic E3 / UC-03)'),
  H3('5.3.1 Description and Priority'),
  P('Maintains parking slots and zones, real-time bay availability status (Available, Occupied, Maintenance), occupied slot protection, and the live occupancy dashboard. Owner: Member 2 (US-09, US-10 Done); Member 4 (US-11, US-12 reassigned 25 Oct 2026). Priority: High.'),
  H3('5.3.2 Stimulus/Response Sequences'),
  B('An administrator adds or updates a slot; the system verifies unique identifier and updates configuration.'),
  B('When a slot state changes, the system ensures atomic single-state transition.'),
  B('An operator opens the dashboard; the system renders real-time occupancy and slot states.'),
  H3('5.3.3 Functional Requirements'),
  tcap('Table 5-3. Parking Facility & Availability Requirements (Epic E3)'),
  frTable(['FR-03','FR-04','FR-07','FR-10']),
  gap(),

  H2('5.4 Reservation Management (Epic E4 / UC-04)'),
  H3('5.4.1 Description and Priority'),
  P('Manages advance parking slot reservations, conflict detection for overlapping time windows, reservation modifications/cancellations, and automated release of unfulfilled holds. Owner: Member 2. Priority: Medium.'),
  H3('5.4.2 Stimulus/Response Sequences'),
  B('A customer requests advance reservation; the system checks schedule conflicts and reserves slot.'),
  B('A customer cancels a reservation before the cutoff; the system marks reservation cancelled and releases the hold.'),
  B('An unfulfilled reservation reaches expiration buffer; the system automatically expires the hold.'),
  H3('5.4.3 Functional Requirements'),
  tcap('Table 5-4. Reservation Management Requirements (Epic E4)'),
  frTable(['FR-19','FR-20','FR-21','FR-22']),
  gap(),

  H2('5.5 Parking Operations (Epic E5 / UC-05, UC-06)'),
  H3('5.5.1 Description and Priority'),
  P('Orchestrates vehicle check-in, compatible slot allocation, single active session enforcement, vehicle check-out, automatic slot release, and immutable parking history retention. Owner: Member 3. Priority: High.'),
  H3('5.5.2 Stimulus/Response Sequences'),
  B('An operator initiates check-in; the system verifies no duplicate active session and assigns an available compatible slot.'),
  B('An operator initiates check-out; the system records exit timestamp, marks session completed, and releases slot to Available.'),
  B('Completed parking records are preserved in historical logs for auditing and reporting.'),
  H3('5.5.3 Functional Requirements'),
  tcap('Table 5-5. Parking Operations Requirements (Epic E5)'),
  frTable(['FR-05','FR-06','FR-08','FR-09','FR-12']),
  gap(),

  H2('5.6 Pricing, Billing & Payment (Epic E6 / UC-07, UC-08)'),
  H3('5.6.1 Description and Priority'),
  P('Configures vehicle-class tariff models, computes duration and fee with grace period evaluation, generates digital slips with QR tokens, and records multi-method payments. Owner: Member 3. Priority: High.'),
  H3('5.6.2 Stimulus/Response Sequences'),
  B('Upon check-in, the system issues a digital parking slip and QR token.'),
  B('Upon check-out, the system computes total billable duration and applies configured tariff.'),
  B('An operator records payment by Cash, Card, or UPI; the system marks invoice paid and issues receipt.'),
  H3('5.6.3 Functional Requirements'),
  tcap('Table 5-6. Pricing, Billing & Payment Requirements (Epic E6)'),
  frTable(['FR-23','FR-24','FR-25','FR-26']),
  gap(),

  H2('5.7 Admin Dashboard & Reporting (Epic E7 / UC-08)'),
  H3('5.7.1 Description and Priority'),
  P('Aggregates facility performance metrics, calculates live occupancy and revenue totals, and generates filterable reports with CSV and PDF export. Owner: Member 4. Priority: Medium.'),
  H3('5.7.2 Stimulus/Response Sequences'),
  B('An administrator opens the executive dashboard; the system loads aggregated metrics and occupancy charts.'),
  B('An administrator selects a date range; the system generates detailed occupancy, throughput, and revenue reports.'),
  B('An administrator triggers export; the system produces structured CSV and PDF files.'),
  H3('5.7.3 Functional Requirements'),
  tcap('Table 5-7. Admin Dashboard & Reporting Requirements (Epic E7)'),
  frTable(['FR-27','FR-28']),
  gap(),

  H2('5.8 Audit, Notifications & Cross-Cutting System Requirements (Epic E8 / UC-09, UC-10)'),
  H3('5.8.1 Description and Priority'),
  P('Maintains an immutable system audit trail, dispatches milestone notifications, validates all client payloads, and enforces standard structured error messaging. Owner: Member 4 / Team. Priority: High.'),
  H3('5.8.2 Stimulus/Response Sequences'),
  B('A sensitive administrative or security action executes; the system records an append-only audit entry.'),
  B('A milestone event occurs (e.g. reservation, payment); the system delivers an in-app notification.'),
  B('An invalid or unauthorized request arrives; the system rejects it with standard structured JSON ({error, code, details}) and standard HTTP status.'),
  H3('5.8.3 Functional Requirements'),
  tcap('Table 5-8. Audit, Notifications & System Requirements (Epic E8)'),
  frTable(['FR-29','FR-30','FR-13','FR-14']),
  gap(),
);

// 6 Business rules
add(H1('6. Business Rules and Domain Requirements'),
  P('BR-01 to BR-07 are carried over from SRS v1.0. BR-08 to BR-14 are derived from the stated FR-15 to FR-30 and add no new behaviour.'),
  table(['ID', 'Business Rule', 'Source & Decision'], [
    ['BR-01', 'A vehicle shall have at most one active parking-slot assignment at any time (anti-passback).', 'FR-06'],
    ['BR-02', 'A parking slot shall be assignable only when its current status is Available.', 'FR-07'],
    ['BR-03', 'A parking slot shall have exactly one current status: Available, Occupied, Maintenance, or Reserved.', 'FR-04, DEC-02'],
    ['BR-04', 'Completing checkout shall automatically release the assigned bay to Available.', 'FR-09'],
    ['BR-05', 'Completed parking sessions shall be retained as immutable historical parking records.', 'FR-12'],
    ['BR-06', 'Parking bay administration shall be restricted to authorized Admin and Operator roles.', 'FR-03, DEC-01'],
    ['BR-07', 'Slot deletion is enforced as soft deactivation (is_active=False) to preserve referential integrity of historical records.', 'FR-03, DEC-03'],
    ['BR-08', 'A bay shall be assigned only to a vehicle whose footprint is compatible with the slot type (Two-Wheeler, Compact, SUV, EV Charging).', 'FR-05, FR-07, DEC-14'],
    ['BR-09', 'Every successful check-in shall issue a digital parking slip and QR token encoding session credentials.', 'FR-25, DEC-08'],
    ['BR-10', 'Parking duration shall enforce a 15-minute entry grace period (0 fee charged if exit <= 15 min), rounded up to next full hour thereafter.', 'FR-24, DEC-06'],
    ['BR-11', 'Fees are evaluated using dynamic vehicle-class tariffs with baseline defaults (₹20/hr Two-Wheeler, ₹40/hr Compact, ₹60/hr SUV) in INR.', 'FR-23, FR-24, DEC-06, DEC-07'],
    ['BR-12', 'Payments shall be recorded as Cash, Card, or UPI upon operator confirmation, issuing a digital receipt.', 'FR-26, DEC-07'],
    ['BR-13', 'A user account shall have exactly one status: active, suspended, or deactivated, modifiable only by an administrator.', 'FR-17, DEC-11'],
    ['BR-14', 'Administrative and security events shall append immutable records to the audit log, retained for 90 days.', 'FR-29, DEC-12'],
    ['BR-15', 'Advance reservations prevent overlapping schedule conflicts and automatically release unfulfilled holds 15 minutes after start time.', 'FR-19, FR-20, FR-22, DEC-15'],
  ], [900, 6526, 1600]),
  gap(),
);

// 7 Data requirements
const FW = [1900, 1500, 3326, 1100, 1200];
const FH = ['Field', 'Data Type', 'Description', 'Mandatory', 'Source'];
add(H1('7. Data Requirements'),
  H2('7.1 Database Requirements'),
  B('PostgreSQL shall be the persistent relational database.'),
  B('Identifiers of users, vehicles, slots, parking records, tickets, and invoices shall be unique within their data sets.'),
  B('Relationships among records shall preserve referential integrity.'),
  B('Active-assignment uniqueness (one slot per vehicle, one vehicle per slot) shall be enforced by database constraints and/or validated model logic (NFR-SAFE-01, NFR-SAFE-02).'),
  B('Check-in and check-out shall execute as atomic transactions (NFR-SAFE-03).'),
  B('Indexes shall support search by license plate and by timestamps (NFR-PERF-03).'),
  B('Passwords shall be stored only as cryptographic hashes (NFR-SEC-05).'),
  H2('7.2 Field Layouts'),
  P('Field lengths and database types are finalized in the database design (TBD). Fields beyond those in SRS v1.0 are derived from the requirement text; any further attribute is TBD.'),
  tcap('Table 7-1. Vehicle'),
  table(FH, [
    ['Vehicle ID', 'Identifier', 'Unique system identifier', 'Yes', 'FR-01'],
    ['Registration (plate) number', 'String', 'License plate; unique; used for search', 'Yes', 'FR-01, FR-11'],
    ['Vehicle type', 'Enum / TBD', 'Vehicle class used for slot compatibility and tariff; values TBD (UD-15)', 'Yes', 'FR-01, FR-24, FR-27'],
    ['Owner information', 'Structured / TBD', 'Owner details; content TBD', 'Yes', 'FR-01'],
    ['Created At / Updated At', 'Date-Time', 'Creation and last-update times', 'Yes', 'SRS v1.0'],
  ], FW), gap(),
  tcap('Table 7-2. Parking Slot, Zone, and Slot Type'),
  table(FH, [
    ['Slot ID', 'Identifier', 'Unique slot identifier', 'Yes', 'FR-03'],
    ['Slot label / number', 'String', 'Human-readable slot reference', 'Yes', 'SRS v1.0'],
    ['Status', 'Enum', 'Exactly one of Available / Occupied / Unavailable or Maintenance (UD-02)', 'Yes', 'FR-04'],
    ['Zone, Floor, Section', 'String / TBD', 'Classification of the slot', 'TBD', 'FR-23'],
    ['Slot type', 'Enum', 'Two-Wheeler, Compact, SUV, EV Charging', 'TBD', 'FR-24'],
    ['Active flag / deactivation', 'TBD', 'Representation of deactivation (UD-03)', 'TBD', 'FR-03'],
  ], FW), gap(),
  tcap('Table 7-3. Parking Record, Ticket, Tariff, and Invoice'),
  table(FH, [
    ['Record ID', 'Identifier', 'Unique parking-session identifier', 'Yes', 'FR-05'],
    ['Vehicle ID / Slot ID', 'Foreign keys', 'Vehicle and slot of the session', 'Yes', 'FR-05'],
    ['Check-in time', 'Date-Time', 'Time of check-in', 'Yes', 'FR-05'],
    ['Check-out time', 'Date-Time / NULL', 'Empty while active', 'No while active', 'FR-08'],
    ['Record status', 'Enum / Boolean', 'Active or completed', 'Yes', 'FR-06, FR-12'],
    ['Duration', 'TBD', 'Computed duration (with grace period)', 'TBD', 'FR-26'],
    ['Ticket / QR token', 'TBD', 'Slip linked to the record; payload TBD (UD-08)', 'Yes (per FR-25)', 'FR-25'],
    ['Tariff', 'TBD', 'Rate rules by vehicle class; flat or dynamic (UD-07)', 'TBD', 'FR-27'],
    ['Invoice / payment', 'TBD', 'Fee, payment method (Cash, Card, UPI), and receipt', 'TBD', 'FR-28'],
  ], FW), gap(),
  tcap('Table 7-4. User, Profile, and Audit Log'),
  table(FH, [
    ['User ID', 'Identifier', 'Unique user identifier', 'Yes', 'FR-15'],
    ['Credentials', 'Hashed secret', 'Login credentials; stored hashed only', 'Yes', 'FR-15, FR-20'],
    ['Role', 'Enum', 'Admin, Operator, or Customer', 'Yes', 'FR-15, FR-18'],
    ['Status', 'Enum', 'active, suspended, or deactivated', 'Yes', 'FR-21'],
    ['Contact details', 'TBD', 'Personal contact details in the profile', 'TBD', 'FR-19'],
    ['Audit record', 'TBD', 'Event type, user, and time at minimum (UD-12)', 'Yes', 'FR-22'],
  ], FW), gap(),
  H2('7.3 Data Retention'),
  P('Completed parking records shall be retained and remain retrievable after checkout (BR-05, FR-12). Retention periods for parking history, audit records, and exported data: TBD (UD-12).'),
  H2('7.4 Reports and Views'),
  table(['Report / View', 'Required Information', 'Source'], [
    ['Current Parking Status', 'Slot identifier, slot status, and associated vehicle information for occupied slots.', 'FR-10'],
    ['Vehicle Parking History', 'Registration number, slot identifier, check-in time, check-out time, and record status.', 'FR-12'],
    ['Revenue and Occupancy Summary', 'Daily and periodic revenue and slot-occupancy summaries with date-range filters.', 'FR-27, FR-28'],
    ['Export', 'Parking logs and business analytics exportable in CSV and PDF formats.', 'FR-28'],
  ], [2400, 5126, 1500]),
  gap(),
);

// 8 NFR
add(H1('8. Non-Functional Requirements'),
  P('Quantitative targets are taken from the RTM. SRS v1.0 left these targets TBD; the RTM values are adopted as agreed. The meaning of "standard load" is TBD (UD-17).'),
  H2('8.1 Performance Requirements'),
  table(['ID', 'Requirement', 'Target', 'Verification'], NFR.slice(0, 3).map(n => [`**${n[0]}**`, n[2] + ` (${n[1]})`, n[4], n[3]]), [1300, 3226, 2500, 2000]),
  gap(),
  H2('8.2 Safety Requirements'),
  table(['ID', 'Requirement', 'Target', 'Verification'], NFR.slice(3, 6).map(n => [`**${n[0]}**`, n[2], n[4], n[3]]), [1300, 3226, 2500, 2000]),
  gap(),
  H2('8.3 Software Quality Attributes'),
  table(['Attribute', 'Requirement', 'Verification'], [
    ['Usability', 'Common parking operations shall present clear actions and meaningful success/error feedback.', 'UI review; system tests.'],
    ['Reliability', 'Successful check-in/check-out shall leave vehicle, parking record, and slot status mutually consistent.', 'Integration and system tests.'],
    ['Maintainability', 'The solution shall separate React UI, Django/DRF application logic, and PostgreSQL persistence.', 'Architecture and code review.'],
    ['Testability', 'Functional rules shall be exposed through deterministic application/API behaviour suitable for automated tests.', 'Unit and integration test review.'],
    ['Portability', 'The web client shall run on a supported modern browser; the version matrix is TBD (UD-17).', 'Compatibility testing.'],
    ['Robustness', 'Invalid inputs and rule violations shall be rejected without corrupting stored parking state.', 'Negative and fault-oriented tests.'],
  ], [1700, 5026, 2300]),
  gap(),
);

// 9 Security
add(H1('9. Security Requirements'),
  H2('9.1 Security Requirements'),
  table(['ID', 'Requirement', 'Target', 'Verification'], NFR.slice(6).map(n => [`**${n[0]}**`, n[2], n[4], n[3]]), [1300, 3226, 2500, 2000]),
  gap(),
  P('Related functional requirements: FR-15 to FR-22 (identity, authentication, authorization, audit) and FR-13 (validation). Details not fixed by the source documents are TBD: hashing algorithm choice between Argon2 and PBKDF2 (UD-09), JWT lifetimes and invalidation mechanism (UD-09), password rules (UD-10), and account recovery (UD-10).'),
  H2('9.2 Role-Based Access Control (Preliminary)'),
  P('The full role-to-function matrix is not specified. Entries below are limited to what the source documents state; all other entries are TBD (UD-01).'),
  table(['Functional Domain / Endpoint', 'Admin', 'Operator', 'Customer', 'Authoritative Source'], [
    ['User account administration & status control', 'Permitted', 'Denied', 'Denied', 'FR-17, DEC-01'],
    ['Bay & zone configuration (add, modify, deactivate)', 'Permitted', 'Permitted', 'Denied', 'FR-03, BR-06, DEC-01'],
    ['Vehicle registration, lookup, & profile maintenance', 'Permitted', 'Permitted', 'Permitted (Own)', 'FR-01, FR-02, FR-11'],
    ['Vehicle check-in, bay allocation, & check-out', 'Permitted', 'Permitted', 'Denied', 'FR-05, FR-08, DEC-01'],
    ['Advance reservation creation & self-cancellation', 'Permitted', 'Permitted', 'Permitted (Own)', 'FR-19, FR-21, DEC-15'],
    ['View real-time bay occupancy dashboard', 'Permitted', 'Permitted', 'Permitted (Public)', 'FR-10, DEC-01'],
    ['Tariff schedule configuration & rate editing', 'Permitted', 'Denied', 'Denied', 'FR-23, DEC-01'],
    ['Payment recording (Cash, Card, UPI) & receipts', 'Permitted', 'Permitted', 'Permitted (View Own)', 'FR-25, FR-26'],
    ['Executive analytics, revenue reports, & exports', 'Permitted', 'Denied', 'Denied', 'FR-27, FR-28, DEC-01'],
    ['System security audit log inspection', 'Permitted', 'Denied', 'Denied', 'FR-29, DEC-12'],
  ], [3000, 1300, 1300, 1926, 1500]),
  gap(),
);

// 10 Error handling
add(H1('10. Error Handling Requirements'),
  P('The system shall reject invalid or conflicting operations, leave stored state unchanged, and return a uniform structured response with a standard HTTP status code and a human-readable message (FR-13, FR-14). The user interface shall display readable feedback. Standard error responses conform to the architecture envelope defined in docs/SAD/Vehicle_Parking_System_SAD.md §5.2.'),
  table(['Scenario', 'Required Behaviour', 'HTTP Status', 'Authoritative Source'], [
    ['Missing, malformed, or invalid input payload', 'Reject before database persistence; identify offending field.', '400 Bad Request', 'FR-13, NFR-SEC-03'],
    ['Unauthenticated, missing, or expired JWT token', 'Reject request; return authentication challenge.', '401 Unauthorized', 'FR-15, NFR-SEC-01'],
    ['Authenticated user lacking required role permission', 'Reject action; preserve system state.', '403 Forbidden', 'FR-16, NFR-SEC-02'],
    ['Vehicle search or entity lookup with no match', 'Return structured not-found response.', '404 Not Found', 'FR-11, FR-14'],
    ['Check-in for a vehicle with an existing active session', 'Reject check-in; abort session creation (anti-passback).', '409 Conflict', 'FR-06, BR-01'],
    ['Check-in or reservation for an occupied/committed bay', 'Reject assignment; preserve existing bay status.', '409 Conflict', 'FR-07, FR-20, BR-02'],
    ['Check-in to a slot with incompatible vehicle class', 'Reject check-in; prompt compatible bay selection.', '400 Bad Request', 'FR-05, BR-08, DEC-14'],
    ['Check-out requested for vehicle without active session', 'Reject checkout; return invalid session error.', '404 Not Found', 'FR-08'],
    ['Partial database failure during check-in/out', 'Execute atomic rollback via transaction.atomic; 0 partial state.', '500 Server Error', 'NFR-SAFE-03'],
    ['Payment recording validation error or payment failure', 'Preserve pending invoice status; display error message.', '422 Unprocessable', 'FR-26'],
  ], [2600, 3226, 1400, 1800]),
  gap(),
);

// 11 Other
add(H1('11. Other Requirements'),
  H2('11.1 Logging and Audit'),
  P('Authentication events and security changes shall be recorded (FR-22, BR-14). Parking sessions shall be retained as a historical audit trail (FR-12). Application error logging for development and maintenance may be defined in design. Audit content and retention: TBD (UD-12).'),
  H2('11.2 Internationalization and Legal'),
  P('No internationalization, regulatory, or legal requirement is specified. Currency, tax, and personal-data handling for owner information and payments are TBD (UD-07).'),
);

// 12 Verification
add(H1('12. Verification Criteria'),
  H2('12.1 Verification Approach'),
  P('Each functional requirement is verified by the RTM test case shown in Section 5 and Appendix B.1 (unit and integration level). System-test identifiers are TBD. Pull-request links in the RTM pipeline are recorded during implementation. Testing and CI/CD compliance are shared by all team members.'),
  table(['Method', 'Description'], [
    ['T: Test', 'Automated or manual execution against the acceptance criteria.'],
    ['I: Inspection', 'Review of code, configuration, or documents (for example CI/CD and CORS configuration).'],
    ['D: Demonstration', 'Operation of the running system (for example the dashboard).'],
    ['A: Analysis', 'Reasoned evaluation (for example indexing and query plans).'],
  ], [2200, 6826]),
  gap(),
  H2('12.2 Non-Functional Verification'),
  table(['ID', 'Verification Strategy', 'Target Criteria'], NFR.map(n => [`**${n[0]}**`, n[3], n[4]]), [1500, 3800, 3726]),
  gap(),
  H2('12.3 Acceptance Criteria for the Baseline'),
  B('All requirements FR-01 to FR-30 have a defined test case and all of them pass.'),
  B('All NFR targets in Section 12.2 are met.'),
  B('Every TBD in Section 13 that affects a requirement under acceptance has been resolved and the SRS updated.'),
  B('Appendix B remains consistent with the RTM.'),
);

// 13 Decision Register and Resolved Baseline Parameters
const RESOLVED_DECISIONS = [
  ['DEC-01','Role Hierarchy & RBAC Matrix','Adopts canonical roles: Admin (full system access), Operator (operations, vehicle, slot, billing), and Customer (self-service profile, reservation, dashboard view). Solves UD-01.','FR-16, FR-18; Sec. 9.2','Member 1'],
  ['DEC-02','Slot Status Vocabulary','Authoritative status values are Available, Occupied, Maintenance, plus Reserved for advance holds (per SAD §3.4.4 and RTM). Solves UD-02.','FR-04, BR-03','Member 2'],
  ['DEC-03','Slot Deletion Policy','Destructive slot deletion is implemented as soft deactivation (is_active=False) to preserve referential integrity of historic parking records. Solves UD-03.','FR-03, BR-07','Member 2'],
  ['DEC-04','Slot Allocation Mode','Semi-automated allocation: system recommends nearest compatible available slot by vehicle class; operator confirms or manually overrides. Solves UD-04.','FR-05','Member 3'],
  ['DEC-05','Exit Verification Mechanism','Operator-driven exit verification via digital parking slip inspection / ticket QR code token scan in terminal. No gate hardware dependency. Solves UD-05.','FR-08','Member 3'],
  ['DEC-06','Grace Period & Duration Rounding','15-minute entry grace period (0 fee charged if exit <= 15 min). After grace period, duration rounds up to next full hour. Solves UD-06.','FR-24, BR-10','Member 3'],
  ['DEC-07','Payment Method Recording & Currency','Supports Cash, Card, and UPI recorded via operator checkout; currency is Indian Rupee (INR / ₹). Solves UD-07 (baseline).','FR-26','Member 3'],
  ['DEC-08','Digital Parking Slip & QR Format','Token contains {sessionId, vehiclePlate, slotNumber, checkInTime, signature} encoded in QR image. Solves UD-08.','FR-25','Member 3'],
  ['DEC-09','JWT Lifetime & Password Hashing','Access token expires in 15 minutes; refresh token expires in 7 days; logout blacklists refresh token. Cryptographic hashing uses PBKDF2 with SHA-256 (Django default). Solves UD-09.','FR-15, NFR-SEC-05','Member 1'],
  ['DEC-10','Password Complexity Policy','Minimum 8 characters with at least 1 uppercase, 1 lowercase, 1 digit, 1 special character. Current password verification required on change. Solves UD-10.','FR-18, NFR-SEC-05','Member 1'],
  ['DEC-11','User Account Lifecycle Semantics','Statuses: active (full access), suspended (login denied with admin notice), deactivated (permanently disabled, soft-deleted). Solves UD-11.','FR-17','Member 1'],
  ['DEC-12','Audit Trail Content & Retention','Logs {event_type, user_id, ip_address, timestamp, details} for security and administrative changes; retained for 90 days. Solves UD-12.','FR-29','Member 4'],
  ['DEC-13','Public Registration Role Safeguard','Public visitor registration creates Customer accounts only. Promotion to Operator or Admin requires explicit Admin action (NFR-SEC-02). Solves UD-13.','FR-15, NFR-SEC-02','Member 1'],
  ['DEC-14','Vehicle Types & Slot Compatibility','Vehicle categories: Two-Wheeler, Compact, SUV, EV Charging. Slots accept matching or smaller footprint; EV Charging reserved for EV-tagged vehicles. Solves UD-15.','FR-01, FR-05, FR-23','Member 2'],
  ['DEC-15','Reservation Cutoff & Hold Expiry','Advance booking up to 7 days ahead; cancellation permitted up to 1 hour prior to start time; unfulfilled holds expire 15 minutes after start time.','FR-19, FR-21, FR-22','Member 2'],
];

const EXTERNAL_DEPENDENCIES = [
  ['EXT-01','Commercial Tariff Rate Schedule','Exact monetary hourly/daily rate schedule per vehicle class requires commercial approval by facility management. Development baseline uses nominal defaults (₹20 Two-Wheeler, ₹40 Compact, ₹60 SUV).','Commercial Authority','FR-23'],
  ['EXT-02','Production Merchant Payment Gateway','Live merchant banking credentials (e.g. Razorpay / UPI Merchant API keys and webhook secrets) require formal corporate entity KYC approval. Core mini-project scope operates with operator transaction recording.','Banking / Payment Provider','FR-26'],
  ['EXT-03','Automated Barrier & ANPR Hardware','Physical gate barrier controllers, loop detectors, and automated number plate recognition (ANPR) cameras require physical site IoT deployment. Classified as post-MVP enterprise extension.','Hardware / Facility Vendor','SAD §3.8'],
];

add(H1('13. Decision Register and Baseline Parameter Specifications'),
  P('To establish an unambiguous, development-ready specification, routine technical decisions have been resolved using secure, sensible defaults aligned with the agile requirements baseline. Items genuinely requiring external business authority or third-party banking/hardware onboarding are recorded with their explicit rationale.'),

  H2('13.1 Resolved Baseline Technical Parameters'),
  table(['Decision ID', 'Topic', 'Resolved Baseline Specification', 'Affects', 'Owner'],
    RESOLVED_DECISIONS.map(d => [`**${d[0]}**`, d[1], d[2], d[3], d[4]]), [900, 1800, 3826, 1400, 1100], { size: 16 }),
  gap(),

  H2('13.2 Genuine External Dependencies & Remaining Open Decisions'),
  P('The following items cannot be settled unilaterally by software engineers as they require commercial authority, banking approval, or physical facility installation:'),
  table(['Dependency ID', 'Topic', 'Description & Blocker Rationale', 'External Stakeholder', 'Affects'],
    EXTERNAL_DEPENDENCIES.map(e => [`**${e[0]}**`, e[1], e[2], e[3], e[4]]), [1100, 2000, 3626, 1300, 1000], { size: 16 }),
  gap(),
);

// Appendix A
add(H1('Appendix A: Glossary'),
  table(['Term', 'Definition'], [
    ['Administrator (Admin)', 'Privileged user permitted to administer slots, zones, and user status.'],
    ['Operator', 'User responsible for operational activities such as check-in and check-out.'],
    ['Customer', 'Authenticated user with limited, role-based access (called Authorized User in SRS v1.0).'],
    ['Parking Slot', 'Uniquely identified place in which a vehicle may be parked.'],
    ['Zone / Floor / Section', 'Classification levels used to group parking slots.'],
    ['Slot Type', 'Vehicle-type constraint of a slot: Two-Wheeler, Compact, SUV, or EV Charging.'],
    ['Available / Occupied / Unavailable / Maintenance', 'Slot status values (see UD-02).'],
    ['Active Parking Record', 'Record of a vehicle that has checked in and not yet checked out.'],
    ['Parking History', 'Completed parking records retained by the system.'],
    ['Ticket / QR Token', 'Digital parking slip issued at check-in.'],
    ['Grace Period', 'Time allowance applied when calculating parking duration (length TBD).'],
    ['Tariff', 'Fee rules by vehicle class, flat-rate or dynamic.'],
    ['Invoice / Receipt', 'Fee statement for a session and proof of payment.'],
    ['JWT', 'JSON Web Token; access/refresh pair issued on authentication.'],
    ['RBAC', 'Role-Based Access Control.'],
    ['RTM', 'Requirements Traceability Matrix.'],
    ['CRUD', 'Create, read, update, delete operations.'],
    ['p95', '95th-percentile response time.'],
    ['ACID', 'Atomicity, consistency, isolation, durability of database transactions.'],
    ['CORS', 'Cross-Origin Resource Sharing.'],
    ['TBD', 'To be determined; see Section 13.'],
  ], [2800, 6226]),
);

// ---------- Appendix B (landscape) ----------
const appB = [];
appB.push(H1('Appendix B: Requirements Traceability Matrix'),
  P('This appendix reproduces the RTM v1.0.0 pipeline: Requirement → User Story → Design → Implementation → Test Case. All status values in the RTM are "Specified". Design and code references are planned locations from the RTM and are not verified here. Pull-request references and system-test IDs: TBD.'),
  H2('B.1 Functional Requirements Traceability'),
  table(['Req ID', 'Requirement Description', 'User Story', 'Module', 'Owner', 'Design Ref', 'Code Ref', 'Test Case', 'Status'],
    RTM.map(r => [`**${r[0]}**`, r[1], r[2], r[3], r[4], r[5], r[6].split('; ').map(x => x), r[7], 'Specified']),
    [800, 2900, 1000, 1400, 800, 2300, 2758, 1000, 1000], { size: 16 }),
  gap(),
  H2('B.2 Non-Functional Requirements Traceability'),
  table(['NFR ID', 'Category', 'Requirement', 'Verification Strategy', 'Target Criteria', 'Status'],
    NFR.map(n => [`**${n[0]}**`, n[1], n[2], n[3], n[4], 'Specified']),
    [1500, 1300, 3600, 3000, 3558, 1000], { size: 16 }),
  gap(),
  H2('B.3 Functional Ownership Summary'),
  table(['Owner', 'Responsibility'], [
    ['Member 1 (Scrum Master and Integration Lead)', 'Epic E1: Identity & Access Management (US-01..04); Epic E2: Vehicle Management (US-05..08); SRS & RTM synchronization; project plan; Git workflow; sprint backlog; integration coordination.'],
    ['Member 2', 'Epic E3: Parking Facility & Availability (US-09, US-10 [Done]; US-11, US-12 reassigned to Member 4 on 25 Oct 2026); Epic E4: Reservation Management (US-13..16).'],
    ['Member 3', 'Epic E5: Parking Operations (US-17..20); Epic E6: Pricing, Billing & Payment (US-21..24).'],
    ['Member 4', 'Epic E7: Admin Dashboard & Reporting (US-25..28); Epic E8: Audit, Notifications & Quality (US-29..32); Reassigned from Member 2 (25 Oct 2026): US-11 (#31, Live Occupancy Dashboard) and US-12 (#32, Slot Integrity Safeguards).'],
    ['All members', 'Validation and error handling; transactional integrity; testing and CI/CD compliance.'],
  ], [4000, 9958], { size: 17 }),
);

// ---------- document ----------
const hdr = new Header({ children: [new Paragraph({
  border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: '808080', space: 4 } },
  tabStops: [{ type: TabStopType.RIGHT, position: PW }],
  children: [run('Vehicle Parking System: Software Requirements Specification', { size: 18, italics: true }), run('\tVersion 1.1', { size: 18, italics: true })] })] });
const hdrL = new Header({ children: [new Paragraph({
  border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: '808080', space: 4 } },
  tabStops: [{ type: TabStopType.RIGHT, position: LW }],
  children: [run('Vehicle Parking System: Software Requirements Specification', { size: 18, italics: true }), run('\tVersion 1.1', { size: 18, italics: true })] })] });
const ftr = w => new Footer({ children: [new Paragraph({
  tabStops: [{ type: TabStopType.RIGHT, position: w }],
  border: { top: { style: BorderStyle.SINGLE, size: 6, color: '808080', space: 4 } },
  children: [run('PES University, Dept. of CSE', { size: 18 }), run('\tPage ', { size: 18 }),
    new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18 }), run(' of ', { size: 18 }),
    new TextRun({ children: [PageNumber.TOTAL_PAGES], font: FONT, size: 18 })] })] });

const A4 = { width: 11906, height: 16838 };
const mar = { top: 1440, right: 1440, bottom: 1300, left: 1440, header: 600, footer: 500 };

const doc = new Document({
  creator: 'Vehicle Parking System Team', title: 'Vehicle Parking System - Software Requirements Specification v1.1',
  features: { updateFields: true },
  styles: {
    default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 32, bold: true, font: FONT, color: NAVY }, paragraph: { spacing: { before: 360, after: 160 }, outlineLevel: 0, keepNext: true } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 26, bold: true, font: FONT, color: NAVY }, paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1, keepNext: true } },
      { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 23, bold: true, italics: true, font: FONT }, paragraph: { spacing: { before: 180, after: 100 }, outlineLevel: 2, keepNext: true } },
    ]
  },
  numbering: { config: [{ reference: 'bul', levels: [
    { level: 0, format: LevelFormat.BULLET, text: '\u2022', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } },
    { level: 1, format: LevelFormat.BULLET, text: '\u2013', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 1080, hanging: 270 } } } } ] }] },
  sections: [
    { properties: { page: { size: A4, margin: mar }, titlePage: true },
      headers: { default: hdr, first: new Header({ children: [new Paragraph({ children: [] })] }) },
      footers: { default: ftr(PW), first: new Footer({ children: [new Paragraph({ children: [] })] }) },
      children: [...cover, new Paragraph({ children: [new PageBreak()] }), ...revision, ...toc, new Paragraph({ children: [new PageBreak()] }), ...body] },
    { properties: { page: { size: { ...A4, orientation: PageOrientation.LANDSCAPE }, margin: mar } },
      headers: { default: hdrL }, footers: { default: ftr(LW) }, children: appB },
  ]
});

const outPath = path.resolve(__dirname, '../docs/requirements/Vehicle_Parking_System_SRS.docx');
Packer.toBuffer(doc).then(b => {
  fs.writeFileSync(outPath, b);
  console.log('SUCCESS: Generated', outPath, 'Bytes:', b.length);
}).catch(err => {
  console.error('ERROR generating DOCX:', err);
  process.exit(1);
});
