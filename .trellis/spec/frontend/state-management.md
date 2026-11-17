# Frontend State Management

## Conventions

- Keep state as local as possible; lift state up only when siblings require synchronization.
- Derived state should be computed, never duplicated into separate mutable variables.
- Asynchronous data fetching must explicitly handle loading, success, empty, and error states.
