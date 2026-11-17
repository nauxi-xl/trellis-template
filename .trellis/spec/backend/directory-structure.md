# Backend Directory Structure & Organization

## Conventions

- Source code resides under `src/` (or package directory).
- Separate internal business logic from public API / transport handlers.
- Keep dependencies directed: APIs depend on services, services depend on models/storage; core models never depend on outer layers.
