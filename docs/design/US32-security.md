# US-32 shared security controls

Issue: [#52](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/issues/52).
This increment provides shared configuration and repeatable verification for
NFR-SEC-01–07. It does not complete the story or implement other members' features.
See [execution evidence](../testing/US32-test-evidence.md) for tested scope.

## Required local setup

After installing backend requirements, generate an environment signing key before
any Django command. From the repository root in PowerShell:

```powershell
$env:DJANGO_SECRET_KEY = & .\.venv\Scripts\python.exe -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
Set-Location backend
..\.venv\Scripts\python.exe manage.py check
..\.venv\Scripts\python.exe manage.py test --verbosity 2
```

The generated value stays in that terminal's environment. For a stable local
session across restarts, store a unique generated value as `DJANGO_SECRET_KEY`
in an ignored root/backend `.env` file. Never commit that file or reuse a key
between environments. Replacing the key invalidates previously issued JWTs and
signed sessions. Blank/missing keys fail startup even in development.

SQLite needs no database password. If PostgreSQL is selected with
`DB_ENGINE=django.db.backends.postgresql`, set `DB_PASSWORD` explicitly alongside
the existing connection variables. A missing/blank password fails startup; there
is no fallback credential. The blank values in `.env.example` must be supplied
locally. Existing demo accounts and test fixture passwords are synthetic local
data; never seed them into a deployed database.

## Transport and browser boundaries

With `DJANGO_DEBUG=False`, Django redirects HTTP to HTTPS and marks session and
CSRF cookies Secure. Development retains HTTP. No reverse-proxy header is trusted
automatically. TLS termination, certificates, HSTS policy and trusted-proxy
configuration remain deployment responsibilities. A terminating proxy must strip
and set forwarded headers itself before a deployment-specific
`SECURE_PROXY_SSL_HEADER` can safely be configured. Test the real deployment for
redirect loops and HTTPS detection before use.

`CORS_ALLOWED_ORIGINS` is a comma-separated exact allowlist. Development defaults
to the two local Vite origins; production defaults to no cross-origin access.
Set the actual HTTPS frontend origin explicitly in production. CORS does not
enable cross-origin cookies. Requests from other origins receive no
`Access-Control-Allow-Origin`; browsers deny the requesting script access.
CORS is not server-side authentication and does not reject every HTTP request.

`CSRF_TRUSTED_ORIGINS` is a separate comma-separated list, empty by default.
Session-authenticated unsafe requests require a valid CSRF token and acceptable
origin. Adding an origin to CORS does not grant it CSRF trust. The existing SPA
uses explicit Bearer JWT headers; this change does not introduce cookie-based
JWTs or change token storage. Anonymous auth endpoints retain their existing
behavior. Django admin continues to use Django's CSRF middleware.

## Verification and traceability

| Requirement | Coverage in this increment | Remaining acceptance work |
| --- | --- | --- |
| NFR-SEC-01/02 | Regression checks for existing authentication and vehicle ownership boundaries; existing role/privilege tests run in the backend suite | US-02 #22 and US-03 #23 complete endpoint/role matrix |
| NFR-SEC-03 | Existing serializer/error suite and a CSRF-valid request reaching payload validation | US-08 #28 and validation for future endpoints |
| NFR-SEC-04 | Environment CORS/CSRF policy, HTTPS redirect and Secure cookie checks | Actual deployment TLS/proxy verification |
| NFR-SEC-05 | Remove fallback signing/database secrets; preserve existing PBKDF2/JWT/revocation behavior and tests | US-04 #24 profile/password flows; deployment secret provisioning |
| NFR-SEC-06 | SQL-like search regression and Bandit high-severity source scan | Browser XSS verification and new endpoint regression |
| NFR-SEC-07 | No audit implementation in this increment | US-29 #49 and real privileged event producers |

The default permission policy, models, migrations, endpoint schemas, role rules,
JWT lifetimes/storage and service interfaces are unchanged. This keeps the shared
work independent of pending domain implementations. The older issue sprint label
is not a security requirement or a statement of completion.

## CI checks and limits

Existing backend jobs generate a fresh ephemeral signing key for each job. The
PostgreSQL service credentials are isolated test credentials. The ordinary Django
suite discovers `common.tests.test_security` from the `backend/` working directory.

The separate `Security verification` workflow runs:

```sh
python -m pip install bandit==1.9.4
python -m bandit -r backend --severity-level high
gitleaks dir . --redact --no-banner
```

Gitleaks 8.30.1 is downloaded from its official release and checked against a
pinned SHA-256. It scans the checked-out files, not past Git history, and redacts
findings. Bandit fails on high-severity Python findings; lower-severity findings
remain visible in its counts. Neither scan proves zero vulnerabilities. Package
advisory scanning, full Git-history scanning and browser penetration testing are
not provided by these jobs. Never suppress a finding solely to obtain green CI.

References: [Django settings](https://docs.djangoproject.com/en/5.2/ref/settings/),
[CORS and CSRF](https://github.com/adamchainz/django-cors-headers#csrf-integration),
[Bandit severity options](https://bandit.readthedocs.io/en/latest/man/bandit.html),
[Gitleaks commands](https://github.com/gitleaks/gitleaks#usage).
