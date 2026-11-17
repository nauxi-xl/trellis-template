# Frontend Development Guidelines

> Development practices, component architecture, state management, and type safety.

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Directory Structure](./directory-structure.md) | Component layout, views/pages, and shared assets | Active |
| [Quality Guidelines](./quality-guidelines.md) | Linting, accessibility, responsiveness, and performance | Active |
| [State Management](./state-management.md) | Single source of truth, reactivity, and persistent state | Active |
| [Type Safety](./type-safety.md) | Strict typing, schema validation, and boundary contracts | Active |

---

## Pre-Development Checklist

- [ ] Check design specs, tokens, and existing shared components before writing new UI
- [ ] Confirm state ownership (local vs global vs URL state)
- [ ] Verify accessibility, responsiveness, and mobile/desktop behavior

---

## Quality Check

- [ ] Linter & type-checker pass with 0 errors
- [ ] Component tests pass
- [ ] No unhandled async errors or missing loading/empty states
