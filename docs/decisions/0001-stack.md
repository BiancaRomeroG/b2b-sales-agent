# ADR 0001: Stack base

Fecha: 2026-10-08. Estado: aceptado.

## Contexto

Agente de ventas B2B por WhatsApp, multi-tenant, con búsqueda híbrida sobre catálogo y tools de
negocio. Debe correr con `docker compose up` y desplegarse en AWS.

## Decisión

| Pieza | Elección | Alternativa descartada | Por qué |
|---|---|---|---|
| Lenguaje | Python 3.12 | — | Ecosistema LLM; requisito de las ofertas |
| Web | FastAPI | Django, Flask | Async nativo para esperar LLMs; validación Pydantic; OpenAPI gratis |
| Paquetes | uv | pip + venv, Poetry | Lockfile reproducible, 10-100x más rápido, una sola herramienta |
| Datos + vectores | Postgres 17 + pgvector | Pinecone, Qdrant | Vectores, catálogo y estado del agente en una sola transacción; filtros en SQL |
| Cache + idempotencia | Redis 7 | tabla en Postgres | `SET NX` con TTL es exactamente el primitivo de idempotencia |
| Contenedores | Docker Compose | instalación manual | Reproducible; el reclutador levanta todo con un comando |
| CI | GitHub Actions | — | Tests de integración contra Postgres y Redis reales en cada push |

## Consecuencias

- Un solo Postgres simplifica, pero pgvector no escala a cientos de millones de vectores. No es el caso.
- Redis añade una pieza. Si cae, la idempotencia falla cerrada: se rechaza hasta que vuelva.
