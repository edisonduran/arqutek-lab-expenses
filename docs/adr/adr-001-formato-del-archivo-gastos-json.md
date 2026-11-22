# ADR-001 · Formato del archivo gastos.json

**Status:** accepted · **Decided by:** E. Muñoz (demo) · **Request:** REQ-architecture-arq-1

## Context

¿Qué estructura tiene gastos.json? Es un contrato persistente difícil de cambiar después.

- Impact: Compatibilidad de datos de usuarios existentes; migraciones futuras.

## Alternatives

- Lista JSON plana de gastos: Pros: Simple, coincide con 'gastos.json vacío' · Cons: Sin versión de esquema; migrar luego es más difícil
- **Objeto {"version":1,"gastos":[...]}** (chosen) — recommended by the agent: Pros: Permite migraciones futuras · Cons: Algo más complejo; el archivo vacío debe definirse

## Decision

Objeto {"version":1,"gastos":[...]}
