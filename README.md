# B2B Sales Agent

Agente conversacional multi-tenant para ventas B2B por WhatsApp. Un comprador escribe, el agente
busca en el catálogo del proveedor con búsqueda híbrida, cotiza, reserva stock y escala a un
vendedor humano cuando no puede resolver.

> En construcción. Plan de 7 días, un commit por entregable. Decisiones en [docs/decisions](docs/decisions).

## Stack

Python 3.12 · FastAPI · LangGraph · PostgreSQL + pgvector · Redis · Twilio WhatsApp · Langfuse · Docker · AWS

## Correr local

```bash
cp .env.example .env
docker compose up --build
curl localhost:8000/health/ready
```

## Desarrollo

```bash
uv sync
docker compose up postgres redis -d
uv run fastapi dev src/app/main.py
uv run pytest                  # unit
INTEGRATION=1 uv run pytest    # unit + integración
uv run ruff check . && uv run ruff format .
```

## Estructura

| Carpeta | Responsabilidad |
|---|---|
| `src/app/api` | Rutas FastAPI |
| `src/app/agent` | Grafo LangGraph, nodos, tools |
| `src/app/search` | Búsqueda híbrida: pgvector + tsvector + filtros |
| `src/app/ingest` | PDF de catálogo a productos estructurados |
| `src/app/channels` | Twilio: webhook, firma, idempotencia |
| `src/app/tenants` | Resolución y aislamiento por tenant |
| `src/app/llm` | Routing y fallback entre modelos |
| `evals` | Dataset y runner de evaluación |
| `docs/decisions` | ADRs: por qué cada decisión |

## Decisiones técnicas

Ver [ADR 0001: Stack base](docs/decisions/0001-stack.md).
