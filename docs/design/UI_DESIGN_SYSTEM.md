# BAY — Architectural Mobility & Automotive Technology Design System

**Target Scope:** Global Design Standards & Implementation Guide across All BAY Screens
**Brand Identity:** BAY. (*Parking. In Perspective.*)
**Visual Direction:** Architectural Elegance + Premium Automotive Technology + Warm Editorial Minimalism
**Document Status:** Active Canonical Design System Specification
**Version:** 2.0.0 (Spatial Mobility Redesign)

---

## 1. Design Philosophy & Product Personality

BAY is an enterprise mobility and intelligent parking management platform. Its visual identity bridges architectural discipline with automotive craftsmanship:

- **Architectural Elegance:** Grounded, warm ivory and white canvas surfaces with crisp structural grid lines, champagne metallic dividers, and generous spatial composure.
- **Premium Automotive Technology:** High-contrast typography, embossed license plate motifs, telemetry badges, and precision status indicators reminiscent of high-end vehicle cockpits and spatial facilities.
- **Warm Editorial Minimalism:** Distinctive sans-serif typography (`DM Sans` + `Manrope`), purposeful editorial copy, restrained color hierarchy, and intentional whitespace.

### Strict Anti-Patterns (What We Avoid)
- **NO Generic Admin Gray:** Avoid sterile, unbranded `#E5E7EB` admin dashboard templates.
- **NO Neon/Cyberpunk Excess:** No glowing cyan/magenta gradients, dark-mode-only neon grids, or decorative blur blobs.
- **NO Rainbow Card Grids:** Colors are not decorative; every surface has a defined functional purpose.
- **NO Color-Only Status:** Status indicators combine color, geometry, text labels, and ARIA roles for full accessibility.
- **NO Ad-Hoc CSS Utilities:** All components strictly consume the centralized design tokens defined in `:root`.

---

## 2. Cohesive Color System & Token Architecture

The BAY palette is built on warm ivory canvas surfaces, crisp elevated white panels, deep midnight blue text, olive green brand accents, champagne dividers, and restrained rose highlights.

### Core Color Palette

| Color Name | Hex Code | Token Name | Semantic Role & Usage |
| :--- | :--- | :--- | :--- |
| **Warm Ivory** | `#F6F3EC` | `--bay-ivory` / `--bay-bg` | Primary application canvas background across all views |
| **White** | `#FFFFFF` | `--bay-white` / `--bay-panel` | Elevated cards, content containers, form input backgrounds |
| **Deep Midnight Blue** | `#23364D` | `--bay-midnight` / `--bay-text-h` | Primary headings, console bars, brand typography, high contrast |
| **Olive Green** | `#687653` | `--bay-olive` / `--bay-accent` | Primary brand accent, primary buttons, active navigation states |
| **Deep Forest Olive** | `#46543D` | `--bay-olive-dark` | Primary button hover state, high-emphasis accent borders |
| **Muted Rose** | `#D99BA8` | `--bay-rose` | Restrained secondary highlight, subtle badges, decorative accents |
| **Champagne** | `#E8D8B8` | `--bay-champagne` | Subtle dividers, luxury metallic micro-borders, highlighted fills |
| **Deep Graphite** | `#30372F` | `--bay-graphite` / `--bay-text` | Readable, warm body text and high-contrast form labels |
| **Muted Graphite** | `#5E665D` | `--bay-graphite-muted` | Secondary helper labels, timestamps, explanatory copy |

### Semantic Parking Status Palette (Explicit & Distinct from Brand)

Brand colors (`#687653` olive) must never be confused with facility operational status:

| Parking State | Base Color | Background Tint | Border Tint | Usage & Description |
| :--- | :--- | :--- | :--- | :--- |
| **AVAILABLE** | `#2A7955` (Emerald) | `#EDF7F2` | `#A3D6BD` | Vacant bay ready for allocation; currently parked vehicle |
| **OCCUPIED** | `#B5473A` (Warm Brick) | `#FDF1EF` | `#F1BBB4` | Active vehicle check-in session; validation conflict error |
| **RESERVED** | `#2A5674` (Cobalt) | `#EEF5F9` | `#B4D1E3` | Pre-booked parking bay or active reservation lock |
| **PENDING** | `#A36F22` (Honey) | `#FEF8ED` | `#ECD2A3` | Awaiting gate check-in or operator verification |
| **INACTIVE** | `#6B6A67` (Slate) | `#F3F2EE` | `#D6D4CF` | Decommissioned, under maintenance, or offline bay |

---

## 3. Typography & Brand Scale

The typographic hierarchy combines **Manrope** for architectural headings and **DM Sans** for legible body text and telemetry data:

```css
--sans: 'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
--heading: 'Manrope', 'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
--mono: 'JetBrains Mono', 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
```

### Type Scale

| Level | Size | Weight | Line Height | Letter Spacing | Font Family | Usage |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Display H1** | `34px–56px` | 600 Semi-Bold | 1.15 | `-2px` | `Manrope` | Login hero statement, spatial floor codes |
| **Section H1** | `28px–38px` | 650 Semi-Bold | 1.20 | `-1.2px` | `Manrope` | Workspace view titles (`Room to move.`) |
| **Card H2** | `22px–26px` | 700 Bold | 1.25 | `-0.8px` | `Manrope` | Card headings, profile view vehicle title |
| **Subhead H3** | `18px–20px` | 650 Semi-Bold | 1.30 | `-0.5px` | `Manrope` | Form headers, modal titles, fleet groups |
| **Body Regular** | `14px–15px` | 400 Regular | 1.55 | `-0.012em` | `DM Sans` | Default paragraphs, specs, explanations |
| **Form Labels** | `12.5px` | 650 Semi-Bold | 1.20 | `0` | `DM Sans` | Form field labels |
| **Micro Eyebrow**| `10px` | 700 Bold | 1.60 | `1.8px` | `DM Sans` | Uppercase category eyebrows |
| **Telemetry Mono**| `14px–19px` | 800 Extra-Bold | 1.20 | `0.8px` | `JetBrains Mono` | License plates, slot codes (`KA-01-AB-1234`) |

---

## 4. Spacing, Elevation & Structural Tokens

### Spacing Scale
- `xxs`: 4px | `xs`: 8px | `sm`: 12px | `md`: 16px | `lg`: 24px | `xl`: 32px | `xxl`: 48px

### Border Radius
- `--radius-xs`: 4px (plate region flags, micro badges)
- `--radius-sm`: 6px (buttons, form inputs, navigation pills)
- `--radius-md`: 10px (content cards, telemetry badges)
- `--radius-lg`: 16px (elevated cards, modal dialogs)
- `--radius-pill`: 9999px (circular status dots, workspace pills)

### Architectural Shadows
- `--bay-shadow-xs`: `0 1px 2px rgba(35, 54, 77, 0.04)`
- `--bay-shadow-card`: `0 2px 10px rgba(35, 54, 77, 0.035), 0 0 0 1px var(--bay-line)`
- `--bay-shadow-card-hover`: `0 8px 24px rgba(35, 54, 77, 0.07), 0 0 0 1px var(--bay-champagne)`
- `--bay-shadow-lg`: `0 14px 34px rgba(35, 54, 77, 0.08), 0 4px 10px rgba(35, 54, 77, 0.04)`

---

## 5. Screen-by-Screen Component Specifications

### 5.1 Authentication (Login & Self-Registration)
- **Split Layout (`.bay-login`):**
  - Left panel (`.bay-login-intro`): Deep midnight blue (`#23364D`) canvas, champagne subtle highlights, warm ivory editorial typography, and isometric deck artwork.
  - Right panel (`.bay-login-form`): Warm ivory background with elevated white card (`#FFFFFF`), champagne border accent, olive primary action button with deep forest hover (`#46543D`).
- **Show/Hide Password:** Native eye toggle button with clear focus outline and hover states.
- **Server Validation:** Accessible alert banner in warm brick red (`#B5473A` / `#FDF1EF`).

### 5.2 Authenticated Workspace Shell (`AuthenticatedView.jsx`)
- **Sidebar (`.bay-sidebar`):**
  - Crisp white background with warm line separator (`#DFDAD0`).
  - Brand mark in Midnight Blue with Olive brand dot.
  - Spatial Workspace location pill in champagne subtle fill with layer icon.
  - Navigation buttons with smooth olive subtle hover and active state in solid olive green with white text and champagne indicator dot.
  - Isometric mini-deck graphic in olive and champagne tones.
  - User footer with avatar monogram, role description, and secure exit button.
- **Topbar (`.bay-topbar`):**
  - White surface with warm border, breadcrumb navigation, and live workspace role badge.
- **Footer (`.bay-footer`):**
  - Minimalist architectural footer with copyright and timestamp.

### 5.3 Vehicle Registration & Fleet Cards (US-05)
- **Registration Form (`.vehicle-reg-card`):**
  - White card with champagne border.
  - Custom embossed license plate input with yellow/ivory plate badge styling.
  - Vehicle type selector chips (Two-Wheeler, Compact, SUV, EV Charging) with distinct icons and olive active state.
- **Fleet Grid (`.vehicles-grid`):**
  - White cards with embossed plate badge, vehicle type badge, registration date, and "View Profile" button.

### 5.4 Vehicle Profile & Telemetry (US-06)
- **Inspector Layout (`.profile-layout-grid`):**
  - Vehicle selector pills on the left with active indicator.
  - Specification grid with champagne dividers, owner details, and registration date.
  - Edit form with inline validation, duplicate conflict prevention, and accessible primary/secondary buttons.

### 5.5 Vehicle Search & Live Status (US-07)
- **Search Bar Card (`.search-bar-card`):**
  - High-precision search bar with uppercase formatting, clear button, and olive search button.
  - Quick-search pills for user's vehicles.
- **Live Status Hero Banner (`.live-status-hero`):**
  - **PARKED:** Emerald status (`#2A7955` / `#EDF7F2`) with pulsing radar animation, slot number, zone, floor level, check-in timestamp.
  - **NOT PARKED:** Slate graphite (`#64748B` / `#F1F5F9`) status.
  - Specification grid and full profile deep link.

### 5.6 Parking Facility & 3D Spatial Deck (US-09 / US-10)
- **Telemetry Bar (`.bay-source-bar`):**
  - Warm ivory background, champagne border, live indicator dot in emerald.
- **Metrics Grid (`.bay-metrics`):**
  - White cards with champagne borders, midnight blue numbers, olive trend indicators.
- **Interactive 3D Stage (`.bay-map-stage`):**
  - Three.js WebGL spatial deck preserved in full functionality with smooth camera controls and floor switcher (B2..L3).
- **2D Plan Grid (`.bay-flat-plan`):**
  - Accessible status styling: Available (emerald), Occupied (warm brick), Reserved (cobalt), Inactive (slate).
- **Slot Editor (`SlotEditor.jsx`):**
  - White modal dialog with champagne line details, olive save button, accessible form controls.

---

## 6. Accessibility & Contrast Compliance

- **Text Contrast:**
  - Midnight Blue (`#23364D`) on Warm Ivory (`#F6F3EC`): **9.8:1** (Exceeds WCAG AAA).
  - Deep Graphite (`#30372F`) on White (`#FFFFFF`): **11.5:1** (Exceeds WCAG AAA).
  - Olive Green (`#687653`) on White text: **4.52:1** (WCAG AA compliant).
  - Deep Forest Olive (`#46543D`) on White text: **7.1:1** (Exceeds WCAG AAA).
- **Focus Rings:** High-visibility 2px solid olive outline with 3px offset for all interactive controls.
- **Motion Reduction:** Full `@media (prefers-reduced-motion: reduce)` support.

---

## 7. Guidelines for Future Contributors

1. **Always Use Tokens:** Never hardcode hex values like `#333` or `#eee`. Use `var(--bay-midnight)`, `var(--bay-ivory)`, `var(--bay-olive)`, etc.
2. **Preserve Operational Semantics:** Never color a parking slot or status indicator with brand colors (`#687653`). Use `--bay-status-available`, `--bay-status-occupied`, `--bay-status-reserved`.
3. **Keep Responsive Breakpoints Intact:** Test all layouts at desktop (>1200px), tablet (820px–1150px), and mobile (<640px).
4. **SVG Icons Only:** Use the centralized `BayIcon` component; do not use emojis as icons.
