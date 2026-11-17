# Frontend Type Safety

## Conventions

- Enable strict type-checking in configuration.
- Avoid `any` or loose type bypasses.
- Validate external API payloads at runtime (e.g. Zod, schema validators) before feeding internal state.
