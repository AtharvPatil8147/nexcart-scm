# NexCart architecture

## Module boundaries

| Area | Responsibility | Do not put here |
| --- | --- | --- |
| `backend/core` | settings, authentication primitives, shared runtime policies | HTTP endpoints or database queries |
| `backend/routers` | request validation, response shape, HTTP status codes | provider-specific integrations or business workflows |
| `backend/agents` | multi-step disruption and nudge workflows | API concerns |
| `backend/services` | external provider adapters (news, weather, shipping, notifications) | database collection names |
| `backend/database` | Mongo connection, indexes, persistence document models | UI or integration logic |
| `backend/utils` | small reusable pure helpers | application configuration |
| `frontend/src/pages` | route-level screens | reusable presentational pieces |
| `frontend/src/components` | reusable UI components | direct API orchestration where a page owns it |
| `frontend/src/api` | HTTP client and API functions | React rendering state |
| `frontend/src/hooks` | reusable React state/effect logic | page-specific layout |

## Dependency direction

`routers / agents → services + database + core` and `services → core + utils`.

Dependencies must not point back into routers or the frontend. Configuration is read through `backend.core.settings`; secrets never belong in source code or logs.

## Data collections

`users`, `skus`, `disruption_events`, `signal_logs`, `customer_profiles`, and `nudge_campaigns` are the system-of-record collections. Derived dashboard metrics should be calculated from these rather than stored separately.
