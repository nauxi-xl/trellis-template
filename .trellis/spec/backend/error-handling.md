# Backend Error Handling & Logging

## Conventions

- Use typed or structured errors for domain failures.
- Never swallow exceptions silently.
- Distinguish between expected client/input errors (validation) and unexpected server/fatal faults.
- Log failures with actionable context (request ID, relevant parameters), never raw sensitive data.
