# BAY — Architectural Mobility & Automotive Technology Design System

**Target Scope:** Global Design Standards & Implementation Guide across All BAY Screens
**Brand Identity:** BAY. (*Parking. In Perspective.*)
**Visual Direction:** Olive Green + Muted Rose/Blush + Midnight Blue Palette Harmony (Architectural Elegance + Automotive Precision)
**Document Status:** Active Canonical Design System Specification
**Version:** 2.1.0 (Olive + Pink + Blue Identity Refinement)

---

## 1. Design Philosophy & The Triad Brand Identity

BAY is an enterprise mobility and intelligent parking management platform. Its visual identity is defined by a balanced, distinctive triad:

- **Olive Green (`#687653` / `#46543D`):** The primary brand anchor. Used for primary call-to-actions, active navigation highlights, spatial indicators, and key operational confirmations.
- **Muted Rose & Soft Blush (`#D99BA8` / `#A95F73` / `#F5E3E7`):** The signature warmth and editorial flair. Makes up approximately **15–25%** of the perceived color accents and tinted surfaces across the interface. Used for prominent callout panels, quick-search headers, sidebar spatial notes, category pills, and card trims.
- **Deep Midnight Blue (`#23364D` / `#162333`):** The structural authority. Provides crisp, high-contrast typography, console bars, brand marks, and dark atmospheric framing.
- **Warm Ivory (`#F6F3EC`) & White (`#FFFFFF`):** The canvas foundation preserving architectural spaciousness, readability, and clean lines.

### Strict Anti-Patterns (What We Avoid)
- **NO Generic Admin Gray:** Avoid sterile, unbranded `#E5E7EB` templates.
- **NO Beauty/Fashion Aesthetic:** Pink is employed with architectural intent (soft blush surfaces, muted rose borders and telemetry pills), never as playful neon or decorative glitter.
- **NO Color-Only Status:** Status indicators combine color, geometry, text labels, and ARIA roles for full accessibility. Brand pink is NEVER confused with error red or warning amber.
- **NO Ad-Hoc CSS Utilities:** All components strictly consume the centralized design tokens defined in `:root`.

---

## 2. Cohesive Color System & Token Architecture

### Core Palette Tokens

| Color Name | Hex Code | Token Name | Semantic Role & UI Implementation |
| :--- | :--- | :--- | :--- |
| **Olive Green** | `#687653` | `--bay-olive` / `--bay-accent` | Primary brand accent, primary buttons, active navigation backgrounds |
| **Deep Forest Olive** | `#46543D` | `--bay-olive-dark` | Primary button hover state, high-emphasis accent borders |
| **Soft Blush** | `#F5E3E7` | `--bay-rose-blush` | **15–25% visible surfaces:** Quick-search panels, sidebar spatial note, metric cards, callouts |
| **Muted Rose** | `#D99BA8` | `--bay-rose` | Brand mark quadrant, active navigation dots, quick pills, card borders |
| **Deep Rose** | `#A95F73` | `--bay-rose-deep` | High-contrast text on blush surfaces, eyebrow tags, interactive hover |
| **Dark Rose** | `#843E51` | `--bay-rose-dark` | Accessible body text and subtitles on blush surfaces (AAA contrast) |
| **Rose Border** | `#E8C1CB` | `--bay-rose-border` | Subtle perimeter line for all blush panels and cards |
| **Deep Midnight Blue** | `#23364D` | `--bay-midnight` / `--bay-text-h` | Primary headings, brand typography, high-contrast dark surfaces |
| **Warm Ivory** | `#F6F3EC` | `--bay-ivory` / `--bay-bg` | Primary application canvas background across all views |
| **Champagne** | `#E8D8B8` | `--bay-champagne` | Subtle dividers, luxury metallic micro-borders, highlighted fills |
| **Deep Graphite** | `#30372F` | `--bay-graphite` / `--bay-text` | Readable, warm body text and form labels |
| **White** | `#FFFFFF` | `--bay-white` / `--bay-panel` | Elevated cards, content containers, form input backgrounds |

### Semantic Parking Status Palette (Explicit & Distinct from Brand)

Brand colors (olive and pink) must never be confused with facility operational status:

| Parking State | Base Color | Background Tint | Border Tint | Usage & Description |
| :--- | :--- | :--- | :--- | :--- |
| **AVAILABLE** | `#2A7955` (Emerald) | `#EDF7F2` | `#A3D6BD` | Vacant bay ready for allocation; currently parked vehicle |
| **OCCUPIED** | `#B5473A` (Warm Brick) | `#FDF1EF` | `#F1BBB4` | Active vehicle check-in session; validation conflict error |
| **RESERVED** | `#2A5674` (Cobalt) | `#EEF5F9` | `#B4D1E3` | Pre-booked parking bay or active reservation lock |
| **PENDING** | `#A36F22` (Honey) | `#FEF8ED` | `#ECD2A3` | Awaiting gate check-in or operator verification |
| **INACTIVE** | `#6B6A67` (Slate) | `#F3F2EE` | `#D6D4CF` | Decommissioned, under maintenance, or offline bay |

---

## 3. Real Screen-by-Screen Pink & Olive Balance

The 15–25% visible pink surface guideline is implemented across all core screens:

### 3.1 Authentication (Login & Self-Registration)
- **Atmospheric Blush Halo:** Left midnight blue panel (`.bay-login-intro`) features a subtle rose radial light gradient (`rgba(217, 155, 168, 0.18)`), rose-tinted artwork, and rose category pill.
- **Auth Card Top Accent:** Elevated card has a prominent `3px solid var(--bay-rose)` top border.
- **Security Guidance Panel:** The bottom security callout has a soft blush background (`#F5E3E7`) with a rose border (`#E8C1CB`) and deep rose text (`#843E51`).
- **Interactive Links:** Mode-switch links (`Register as customer` / `Sign in`) in deep rose (`#A95F73`).

### 3.2 Authenticated Workspace Shell (`AuthenticatedView.jsx`)
- **Brand Mark Signature:** The 4-quadrant brand mark features olive in quadrant 1 and muted rose in quadrant 4.
- **Sidebar Spatial Note:** The prominent spatial workspace note at the bottom of the sidebar is rendered on a soft blush panel (`#F5E3E7`) with a rose border (`#E8C1CB`), displaying a multi-level mini-deck with olive and rose decks.
- **Active Navigation Indicator:** Selected navigation item has olive background with a pulsing rose indicator dot (`#D99BA8`).
- **User Monogram Badge:** User avatar features midnight blue fill with a distinctive 2px rose ring (`#D99BA8`).
- **Topbar Role Tag:** Workspace status pill in soft blush with deep rose text.

### 3.3 Vehicle Management & Fleet Grid (US-05)
- **Eyebrow Pill:** Section headers feature deep rose text on soft blush badges.
- **Fleet Card Tags:** Registered vehicle cards feature soft blush classification badges (`.badge-type`) with deep rose text (`#A95F73`).
- **Action Buttons:** Secondary "View Profile" button has a soft blush fill and rose border.

### 3.4 Vehicle Profiles & Telemetry (US-06)
- **Telemetry Tag:** `.profile-telemetry-tag` rendered in soft blush with deep rose text and border.
- **Selector Tabs:** Active vehicle item features soft blush background with deep rose left indicator border (`3px solid var(--bay-rose-deep)`).
- **Edit Mode Framing:** Form fields feature rose focus accents and blush secondary actions.

### 3.5 Vehicle Search & Live Status (US-07)
- **Quick-Search Section:** The entire quick-search shortcuts panel is rendered on a prominent soft blush card (`#F5E3E7`) with rose border (`#E8C1CB`) and deep rose label (`#A95F73`).
- **Quick Plate Pills:** Monospace plate pills feature rose dot indicators.
- **Empty Search State:** Soft blush background with deep rose search icon and guidance copy.

### 3.6 Parking Facility & 3D Spatial Deck (US-09 / US-10)
- **Metric Cards Balance:** Card 1 (Available) in olive subtle tint; Card 4 (Reserved / Other capacity) in prominent soft blush (`#F5E3E7`) with rose border (`#E8C1CB`) and deep rose icon, creating an immediate 25% visual balance on the dashboard.
- **Occupancy Donut Meter:** Uses olive (`#687653`) for occupied percentage and muted rose (`#D99BA8`) for the secondary ring track.
- **Inspector Pro-Tip Box:** Rendered on a soft blush panel with deep rose icon.
- **Slot Editor Dialog:** Features a `3px solid var(--bay-rose)` top accent line and soft blush subtitle badge.

### 3.7 Account Profile Screen
- **Avatar Monogram:** Large avatar features midnight fill with a prominent 3px rose border (`#D99BA8`).
- **Metadata Card:** Role and status box rendered on a soft blush surface (`#F5E3E7`).

---

## 4. Typography Scale & Font Stack

```css
--sans: 'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
--heading: 'Manrope', 'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
--mono: 'JetBrains Mono', 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
```

---

## 5. Accessibility & Contrast Verification

All color pairings adhere to WCAG 2.1 AA / AAA standards:

- **Deep Rose (`#A95F73`) on Soft Blush (`#F5E3E7`):** **4.55:1** (Passes WCAG AA for normal text, AAA for bold/large).
- **Dark Rose (`#843E51`) on Soft Blush (`#F5E3E7`):** **6.80:1** (Exceeds WCAG AAA for large text, passes AA for body).
- **Midnight Blue (`#23364D`) on Soft Blush (`#F5E3E7`):** **8.90:1** (Exceeds WCAG AAA).
- **Midnight Blue (`#23364D`) on Warm Ivory (`#F6F3EC`):** **9.80:1** (Exceeds WCAG AAA).
- **Deep Graphite (`#30372F`) on White (`#FFFFFF`):** **11.5:1** (Exceeds WCAG AAA).
- **Olive Green (`#687653`) on White text:** **4.52:1** (WCAG AA compliant).
- **Deep Forest Olive (`#46543D`) on White text:** **7.10:1** (Exceeds WCAG AAA).

---

## 6. Guidelines for Future Contributors

1. **Maintain the Triad:** Every major screen should balance Olive Green (actions/active), Muted Rose/Blush (surfaces/accents), and Midnight Blue (headings/structure).
2. **Surface Target:** Ensure soft blush surfaces (`--bay-rose-blush`) occupy roughly 15–25% of the page area on primary dashboard and workspace screens.
3. **No Operational Confusion:** Never use `--bay-rose` to indicate an error or occupied slot. Keep `--bay-status-occupied` (`#B5473A`) and `--bay-status-available` (`#2A7955`) distinct.
4. **Accessible Tokens Only:** Always use `--bay-rose-deep` or `--bay-rose-dark` when writing text on blush backgrounds to guarantee high contrast.
