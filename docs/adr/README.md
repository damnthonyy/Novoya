# Architecture decision records

One short file per decision that shapes Novoya: the context, what we decided, and what it
changes. To add one, copy [0000-template.md](0000-template.md) to the next number and add it
below. An accepted ADR is never rewritten to change the decision: a new ADR replaces it.

| # | Decision | Status |
|---|---|---|
| [0001](0001-use-fastapi.md) | Use FastAPI for the backend | Accepted |
| [0002](0002-modular-monolith.md) | One repository, and a modular monolith with Clean Architecture | Accepted |
| [0003](0003-no-past-trips-import.md) | No import of the client's past trips (GDPR) | Accepted |
| [0004](0004-in-process-travel-tools.md) | Travel tools as in-process functions, not an MCP server | Accepted |
| [0005](0005-openrouter-llm.md) | OpenRouter as the LLM provider | Accepted |
| [0006](0006-negotiated-prices-pdf-quote.md) | No fixed prices: a human agent negotiates and sends a PDF quote | Accepted |
| [0007](0007-server-side-sessions.md) | Opaque server-side sessions, not JWT | Accepted |
| [0008](0008-account-linking.md) | One account per email, linked across Google and password | Accepted |
| [0009](0009-roles.md) | Three roles stored on the user: client, agent, admin | Accepted |
| [0010](0010-email-password-sign-in.md) | Sign-in with email and password, next to Google | Accepted |
