# ADR 0002: Modelo de datos multi-tenant y embeddings locales

Fecha: 2026-10-08. Estado: aceptado.

## Contexto

Cada proveedor (tenant) tiene su catálogo, su número de WhatsApp y sus conversaciones. El agente
necesita buscar productos por significado y por código exacto. Anthropic no ofrece API de embeddings.

## Decisiones

| Tema | Elección | Alternativa descartada | Por qué |
|---|---|---|---|
| Aislamiento | Columna `tenant_id` en toda tabla + filtro obligatorio en cada query | Schema o base por tenant | Suficiente para decenas de tenants; una sola migración; RLS se suma en el día 2 como segunda barrera |
| Resolución de tenant | Por número de WhatsApp destino | Por un id en el body | El usuario no controla el número destino; sí controla el body |
| Keyword search | Columna `search_text` tsvector generada por Postgres, índice GIN | Calcularla en la app | Siempre sincronizada, cero código, configuración `spanish` con stemming |
| Vector search | `embedding vector(384)` con índice HNSW coseno | IVFFlat | HNSW no necesita entrenamiento y consulta más rápido; memoria irrelevante a este tamaño |
| Modelo de embeddings | `paraphrase-multilingual-MiniLM-L12-v2` vía fastembed (ONNX) | sentence-transformers (PyTorch), OpenAI embeddings | Sin API key, datos no salen de la infra, sin torch: imagen ~100 MB en vez de ~2 GB. Español cubierto |
| Qué se embebe | nombre + categoría + descripción | Todo el registro | SKU y precio no tienen semántica; meterlos agrega ruido. El SKU lo cubre tsvector |
| Extracción desde PDF | Claude con tool calling forzado a un schema Pydantic | Pedir JSON en el prompt | El schema valida antes de persistir; filas inválidas se reportan, no se insertan |
| Carga | `INSERT ... ON CONFLICT (tenant_id, sku) DO UPDATE` | Borrar y reinsertar | Idempotente: re-ingestar el mismo archivo no duplica ni pierde ids |
| Migraciones | Alembic async, escritas a mano | `create_all` | Extensión, columna generada e índice HNSW no salen bien del autogenerate |

## Consecuencias

- El modelo local pesa ~470 MB en disco y tarda segundos en cargar. Se carga una vez por proceso.
- Cambiar de modelo de embeddings obliga a reindexar todo el catálogo: la dimensión está en el schema.
- Un PDF escaneado sin capa de texto no se procesa todavía. OCR queda fuera del alcance de la semana.
