# Backend Development Guidelines

> Core conventions, architectural patterns, and error contracts for backend services and core logic.

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Directory Structure](./directory-structure.md) | Source layout, module responsibilities, and dependency rules | Active |
| [Error Handling](./error-handling.md) | Standardized error types, boundary exception safety, and logging | Active |
| [Quality Guidelines](./quality-guidelines.md) | Linting, type-checking, test conventions, and verification gates | Active |

---

## Pre-Development Checklist

- [ ] Reviewed relevant thinking guides under `.trellis/spec/guides/`
- [ ] Confirmed error boundaries and exception propagation
- [ ] Checked for existing utilities before adding new helpers
- [ ] Verified database / network transaction and boundary safety

---

## Quality Check

- [ ] Linter & type-checker pass with 0 errors
- [ ] Unit & integration tests pass cleanly
- [ ] No raw/unhandled debug prints left in hot paths
