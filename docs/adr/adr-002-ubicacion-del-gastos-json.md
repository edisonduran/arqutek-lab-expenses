# ADR-002 · Ubicación del gastos.json

**Status:** accepted · **Decided by:** E. Muñoz (demo) · **Request:** REQ-architecture-arq-2

## Context

¿Dónde se busca gastos.json por defecto?

- Impact: Dónde viven los datos del usuario; afecta pruebas y uso diario.

## Alternatives

- **./gastos.json en el directorio actual, con override GASTOS_FILE** (chosen) — recommended by the agent: Pros: Simple, coincide con los requisitos, fácil de aislar en tests · Cons: Distintos directorios dan distintos archivos
- ~/.gastos/gastos.json: Pros: Una única fuente de datos · Cons: Escribe fuera del proyecto; requisitos no lo piden

## Decision

./gastos.json en el directorio actual, con override GASTOS_FILE
