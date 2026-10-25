# Vehicle Parking System — Frontend Design System Specification

**Target Scope:** Global Design Standards & Implementation Guide for Sprint 1 & Sprint 2 User Stories  
**Lead Author / Scrum Master:** Member 1 (`Trisha-Vallamkonda-Prathap`)  
**Applicable User Stories:** US-01 (Authentication), US-05 (Vehicle Registration), US-06 (Vehicle Profile & Update), and all downstream modules (US-02..US-04, US-07..US-32)  
**Status:** Active Canonical Specification  
**Version:** 1.0.0 (Automotive Telemetry Baseline)  

---

## 1. Design Philosophy & Product Personality

The Vehicle Parking System user interface is modeled on **high-precision automotive technology, telemetry dashboards, and modern industrial SaaS platforms**. It communicates:
- **Trust & Operational Reliability:** Mission-critical clarity for facility operators and drivers.
- **Automotive Craftsmanship:** High-contrast, clean typography, license-plate-inspired data badges, and restrained visual structure.
- **Confident Modern Technology:** Crisp 1px borders, purposeful elevation, and deliberate accent colors rather than generic AI-dashboard gradients.
- **Uncompromised Usability:** Immediate visual scanning, legible high-contrast states, and accessible touch targets.

### Explicit Anti-Patterns (What We Avoid)
- **NO Purple/Violet Primaries:** Avoid default Vite/AI template purple (`#AA3BFF`, `#7C3AED`, `#C084FC`).
- **NO Rainbow Gradients:** No purple-pink-blue mesh gradients or decorative blur blobs.
- **NO Heavy Glassmorphism:** Avoid low-contrast translucent cards that degrade text legibility.
- **NO Oversized Pill Shapes or Toy Aesthetics:** Corner radii are restrained and purposeful; inputs and cards feel engineered, not playful.
- **NO Ad-Hoc Styling:** All views must consume the standard tokens defined in `:root`.

---

## 2. Canonical Color Palette & Tokens

The palette is anchored by deep maritime navies, clean off-white canvas surfaces, and deliberate high-visibility warm accents.

| Token Name | Hex Code | Intended Semantic Use |
| :--- | :--- | :--- |
| `--color-primary-navy` | `#14283F` | Primary brand tone, primary buttons, console headers, active headings |
| `--color-deep-navy` | `#0C1828` | High-emphasis surfaces, button hover states, app header border |
| `--color-slate-blue` | `#35546D` | Secondary emphasis, category badges, focus outlines, subtle icons |
| `--color-warm-off-white` | `#F7F6F2` | Global application canvas background (`body`, page containers) |
| `--color-pure-white` | `#FFFFFF` | Form surfaces, elevated content cards, input field backgrounds |
| `--color-main-text` | `#172536` | High-contrast primary text, labels, inputs, strong headers |
| `--color-muted-text` | `#687586` | Secondary labels, timestamps, explanatory notes, icons |
| `--color-border` | `#E1E5E8` | Card perimeter borders, standard form input outlines, dividers |
| `--color-border-subtle` | `#ECEFF1` | Table row dividers, secondary sub-card outlines, pill borders |
| `--color-coral-red` | `#E65B52` | Primary warm accent, active indicator highlights, operational badges |
| `--color-warm-orange` | `#F29A52` | Secondary accent, SUV/heavy class badges, pending states |
| `--color-restrained-rose` | `#D96B83` | Micro-accent details, EV charging highlights, subtle telemetry tags |
| `--color-success-green` | `#21845A` | Success alerts, active session dots, available slot badges |
| `--color-warning-amber` | `#A96512` | Warning banners, approaching expiration, cautionary prompts |
| `--color-error-red` | `#B93838` | Validation errors, conflict warnings (409), destructive actions |

---

## 3. Semantic Action & Surface Color Mapping

Teammates must apply color tokens according to these strict functional roles:

- **Primary Actions (Submit, Confirm, Register, Save):**
  - Normal: Background `var(--color-primary-navy)` (`#14283F`), text `var(--color-pure-white)` (`#FFFFFF`).
  - Hover: Background `var(--color-deep-navy)` (`#0C1828`).
  - Disabled: Background `var(--color-slate-blue)` with opacity `0.6`, cursor `not-allowed`.
- **Secondary Actions (Cancel, Secondary Nav, Test Routes):**
  - Background `var(--color-pure-white)`, border `1px solid var(--color-border)`, text `var(--color-main-text)`.
  - Hover: Background `var(--color-border-subtle)`, border `#CBD3D8`.
- **Destructive Actions (Logout, Revoke, Delete, Terminate):**
  - Border `1px solid rgba(185, 56, 56, 0.35)`, background `var(--color-pure-white)`, text `var(--color-error-red)`.
  - Hover: Background `#FDF3F3`, border `var(--color-error-red)`.
- **Surfaces & Cards:**
  - Base Page: `var(--color-warm-off-white)` (`#F7F6F2`).
  - Card Body: `var(--color-pure-white)` (`#FFFFFF`) with `1px solid var(--color-border)`.
  - Telemetry Banners: `#F4F6F8` with subtle border.

---

## 4. Typography & Font Hierarchy

The interface utilizes the system's native modern font stack for crisp rendering without external font download latency:

```css
--sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
--heading: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
--mono: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace;
```

### Hierarchy Scale

| Element | Size | Weight | Line Height | Color | Usage |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **H1** | `1.5rem` (24px) | 700 (Bold) | 1.25 | `#172536` | Top-level section / page titles |
| **H2** | `1.25rem` (20px) | 600 (Semi-bold) | 1.25 | `#172536` | Card headers, form titles |
| **H3** | `1.10rem` (17.6px) | 600 | 1.30 | `#14283F` | Sub-section headers (e.g., Fleet List) |
| **H4** | `0.95rem` (15.2px) | 600 | 1.35 | `#14283F` | Widget headers, modal headers |
| **Body Text** | `0.90rem` (14.4px) | 400 (Regular) | 1.50 | `#172536` | Standard descriptions, copy |
| **Field Label** | `0.82rem` (13.1px) | 600 | 1.20 | `#172536` | Form input labels |
| **Micro Caption** | `0.75rem` (12px) | 500 / 600 | 1.30 | `#687586` | Helper text, timestamps, tags |
| **Monospace** | `0.88rem` (14px) | 700 | 1.20 | `#0C1828` | License plates, tokens, IDs |

---

## 5. Spacing Scale & Layout Rules

Layouts adhere to an 8-point baseline grid with a 4px half-step for micro-elements:

```css
--space-2xs: 0.25rem; /* 4px */
--space-xs:  0.50rem; /* 8px */
--space-sm:  0.75rem; /* 12px */
--space-md:  1.00rem; /* 16px */
--space-lg:  1.50rem; /* 24px */
--space-xl:  2.00rem; /* 32px */
--space-2xl: 2.50rem; /* 40px */
```

### Layout Principles
- **Page Container:** Centered with max-width `1140px` and responsive horizontal padding (`1rem` on mobile, `2rem` on desktop).
- **Card Padding:** `2rem` for full auth/console cards; `1rem` to `1.25rem` for sub-cards and grid elements.
- **Form Gaps:** `1.15rem` between form groups; `0.4rem` between label and input.
- **Form Rows:** Side-by-side inputs on screens `> 640px` using `.form-row` and `.col-half`; stacks vertically on mobile.

---

## 6. Border Radius & Shadow Rules

Avoid round pill buttons and cartoonish bubbly curves. Radius values are calibrated for industrial hardware:

```css
--radius-sm: 4px;   /* Input fields, micro-badges, license plate boxes */
--radius-md: 6px;   /* Standard action buttons, alert banners */
--radius-lg: 10px;  /* Cards, modals, major elevation panels */
```

### Elevation & Shadows
- **Card Ambient Elevation:**
  ```css
  --shadow-sm: 0 1px 2px rgba(12, 24, 40, 0.05);
  --shadow:    0 2px 8px rgba(12, 24, 40, 0.06), 0 1px 2px rgba(12, 24, 40, 0.04);
  --shadow-lg: 0 12px 28px rgba(12, 24, 40, 0.08), 0 2px 6px rgba(12, 24, 40, 0.04);
  ```
- **Active Card Indicator:** Cards may have a subtle top accent bar (`height: 4px`) gradient from Navy `#14283F` to Coral `#E65B52`.

---

## 7. Button Variants & Interaction States

All buttons share a base class (`.btn-primary`, `.btn-secondary`, `.btn-danger`):

```html
<!-- Primary Button -->
<button type="submit" class="btn-primary" id="btn-save">
  Save Record
</button>

<!-- Secondary / Cancel Button -->
<button type="button" class="btn-secondary" id="btn-cancel">
  Cancel
</button>

<!-- Destructive Action Button -->
<button type="button" class="btn-danger" id="btn-delete">
  Deactivate Record
</button>
```

### Interactive State Requirements
- **Hover:** Primary darkens to `#0C1828`. Secondary shifts background to `#ECEFF1`.
- **Focus:** 3px ring using `rgba(53, 84, 109, 0.15)`. No default browser blue or purple outlines.
- **Active:** Slight `1px` downward translation (`transform: translateY(1px)`).
- **Loading:** Display inline `.spinner` or `.btn-spinner` (14px rotating circle) and text "Saving...". Set `disabled={true}` to prevent duplicate clicks.

---

## 8. Inputs, Forms & Validation Messaging

### Input Structure
Form inputs must always pair with an explicit `<label htmlFor="field-id">` and display an asterisk for mandatory entries:

```jsx
<div className="form-group">
  <label htmlFor="slot_number">
    Slot Identifier <span className="required">*</span>
  </label>
  <input
    id="slot_number"
    name="slot_number"
    type="text"
    className={`form-input ${fieldErrors.slot_number ? 'input-error' : ''}`}
    placeholder="e.g. A-101"
    required
  />
  {fieldErrors.slot_number && (
    <span className="field-error-text" id="slot-error">
      {fieldErrors.slot_number.join(' ')}
    </span>
  )}
</div>
```

### Validation Styling
- **Error State (`.input-error`):** Border switches to `var(--color-error-red)` (`#B93838`) with soft `#FFFDFD` tint.
- **Inline Message (`.field-error-text`):** Small `0.75rem` text beneath the input in `#B93838`.

---

## 9. Cards, Badges, Lists & Feedback States

### 1. License Plate Badge Card (US-05, US-06 Pattern)
Vehicle and parking slot records should present identifier plates with stamped monospace styling:

```html
<div class="vehicle-badge-card" id="card-1">
  <div class="vehicle-card-top">
    <div class="vehicle-plate font-mono">KA-01-AB-1234</div>
    <button type="button" class="btn-edit-badge">✏️ Edit</button>
  </div>
  <div class="vehicle-meta">
    <span class="badge-type">Compact</span>
    <span class="owner-tag">👤 Jane Doe</span>
  </div>
</div>
```

### 2. Vehicle Class & Status Badges
- **Two-Wheeler / Operator:** `background: rgba(53, 84, 109, 0.12)`, `color: #35546D`
- **Compact / Admin:** `background: rgba(20, 40, 63, 0.12)`, `color: #14283F`
- **SUV / Warning:** `background: rgba(242, 154, 82, 0.12)`, `color: #9C5A1A`
- **EV Charging / Active Session:** `background: rgba(33, 132, 90, 0.12)`, `color: #21845A`

### 3. Alert Banners (US-31 Standard)
```html
<div class="alert-banner alert-error" role="alert">
  <span class="alert-icon">⚠️</span>
  <span class="alert-text">A vehicle with this registration number already exists.</span>
</div>
```

---

## 10. Responsive Breakpoints

The application utilizes three standard responsive breakpoints:
1. **Desktop / Widescreen (`>= 1024px`):** Full two-column dashboard layouts, multi-column form rows, wide fleet grids (`minmax(260px, 1fr)`).
2. **Tablet (`640px` to `1023px`):** Single-column dashboard containers with side-by-side inputs preserved where legible.
3. **Mobile (`< 640px`):**
   - `.form-row` automatically wraps to full width column.
   - Action buttons expand to `width: 100%`.
   - Card padding reduces from `2.25rem` to `1.25rem`.
   - Header title compresses to `1.15rem`.

---

## 11. Accessibility & Contrast Compliance

- **WCAG AA Compliance:** All text meets or exceeds a `4.5:1` contrast ratio against its background.
  - Primary text `#172536` on `#F7F6F2` background achieves `12.3:1`.
  - Coral accent `#E65B52` is used for iconography and badges, while interactive text uses `#FFFFFF` on Navy `#14283F` (`14.1:1`).
- **Focus Rings:** All keyboard navigation (`Tab` key) triggers a visible, clean 3px focus ring with `rgba(53, 84, 109, 0.15)`.
- **Screen Reader Support:** Interactive icons provide `aria-hidden="true"` or paired `aria-label` tags. Loading states indicate `aria-busy="true"` on parent forms.

---

## 12. Component & CSS Naming Conventions

Teammates must adhere to structured, semantic CSS class naming:
- `.btn-*` for buttons (`.btn-primary`, `.btn-secondary`, `.btn-danger`, `.btn-sm`).
- `.form-group` for field label/input wrappers.
- `.form-input` for text, email, password, and select elements.
- `.alert-banner`, `.alert-error`, `.alert-success` for US-31 status banners.
- `.badge-*` for categorized tags.
- Avoid utility cascades or inline CSS style objects in React components.

---

## 13. Examples of Correct vs. Incorrect Usage

### Correct Examples
```css
/* ✅ DO: Consume semantic tokens */
.slot-card {
  background-color: var(--color-pure-white);
  border: 1px solid var(--color-border);
  color: var(--color-main-text);
  border-radius: var(--radius-md);
}

.slot-action-btn {
  background-color: var(--color-primary-navy);
  color: var(--color-pure-white);
}
```

### Incorrect Examples
```css
/* ❌ DO NOT: Use arbitrary purple or neon gradients */
.slot-card {
  background: linear-gradient(135deg, #a855f7 0%, #ec4899 100%); /* NO purple/pink gradients */
  border-radius: 9999px; /* NO oversized bubbly pills for cards */
  box-shadow: 0 20px 50px rgba(168, 85, 247, 0.5); /* NO neon glows */
}

/* ❌ DO NOT: Hardcode ad-hoc hex values */
.slot-action-btn {
  background: #3b82f6; /* Use var(--color-primary-navy) instead */
}
```

---

## 14. Professionalism & Visual Discipline

- **Restraint Over Decoration:** Do not add decorative circles, floating gradient blobs, or 3D cards.
- **Data-First Layout:** Prioritize clear data visibility (slot status, vehicle plates, timestamps).
- **Purposeful Color:** Every color communicates meaning (Green = Active/Available, Amber = Warning, Red = Conflict/Error, Navy = Primary Identity).

---

## 15. Teammate Implementation Checklist (Zero Breaking Changes)

When implementing your story's UI:
1. **Preserve Story Boundaries:** Style only your assigned pages and components (e.g. Member 2 styles `Slots.jsx`, Member 3 styles `Operations.jsx`, Member 4 styles `Dashboard.jsx`).
2. **Import Shared CSS:** Ensure `import '../App.css'` is present in your page or main entry.
3. **Use Standard Element Classes:** Wrap forms in `.auth-form` or `.vehicle-form`, wrap fields in `.form-group`, and style buttons with `.btn-primary` and `.btn-secondary`.
4. **Preserve IDs for Testing:** Never remove or rename HTML `id` attributes that automated test suites rely upon.
5. **Run Lint and Build:** Execute `npm test`, `npm run lint`, and `npm run build` to confirm your changes pass all checks.
