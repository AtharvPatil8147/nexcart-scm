# NexCart project to-do

This is the living delivery list for the project. New requests will be added here as they are agreed.

## In progress

- [x] **Authentication and RBAC** — sign-in, bootstrap administration, protected API routes, and role-aware navigation.
- [x] **News corroboration** — collect matching supply-chain reports from more than one source; record source coverage, a genuineness assessment, and severity for every news signal.

## Next

- [ ] Add user administration (invite, deactivate, change role, audit log).
- [ ] Add tests for authentication/authorization and news-verification scoring.
- [ ] Add monitoring for news-provider failures and rate limits.
- [ ] Recreate the stale Python virtual environment, install backend dependencies, and run the backend test suite.
- [ ] Restore a runnable backend runtime: install Python 3.14 or recreate dependencies for Python 3.12; Docker Desktop's Linux engine is currently unavailable.
- [ ] Fix the manual signal form/API contract: the current form sends display fields, while the API expects a `raw_payload` object.
- [ ] Split the frontend production bundle; it currently exceeds Vite's 500 kB warning threshold.

## Completed

- [x] Initial project health assessment — 20 November 2026.
- [x] Centralised runtime configuration and documented module/data boundaries — 20 November 2026.
- [x] Audited `.env` structure and security-sensitive configuration — 20 November 2026.
- [x] Normalised `backend/requirements.txt` to ASCII so Windows pip can read it — 22 November 2026.
