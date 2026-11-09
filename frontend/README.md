# Vehicle Parking System frontend

React 19 and Vite 8 client for JWT sign-in/registration, vehicle registration/profile/search, facility management, public parking availability, account administration, admin dashboard/report exports and in-app notifications. Styling uses local CSS; the facility visualization uses Three.js. Current requests use browser fetch with relative `/api` URLs; the Vite development proxy targets `http://127.0.0.1:8000`.

## Development

Start Django using the [root setup guide](../README.md#run-locally). From this directory with Node.js 22:

```sh
npm ci
npm run dev
```

Open the URL Vite prints, normally `http://localhost:5173`. Customer registration is available from sign-in. Anonymous visitors can open Parking availability; management views require an active Admin or Operator account. Availability exposes no vehicle identities and refreshes every 30 seconds or manually.

## Checks

```sh
npm test
npm run lint
npm run build
```

The production build writes `dist/`. `npm run preview` previews static assets; it does not provide a production Django API proxy. Configure the serving environment to route `/api` to Django. This repository does not establish a production deployment.

## Current interfaces

The workspace includes profile/password, administrative users, dashboard/export and notification views. Parking entry/exit, reservations, history, tariffs, audit and receipt workflows have documented backend APIs. See the [current SAD](../docs/SAD/Vehicle_Parking_System_SAD.md), [UI design system](../docs/design/UI_DESIGN_SYSTEM.md) and [final verification](../docs/testing/FINAL_VERIFICATION_REPORT.md).
