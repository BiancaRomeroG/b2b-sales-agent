"""Local embeddings via fastembed (ONNX). No API key, no PyTorch, ~470 MB model cached on disk.

Why local: Anthropic has no embeddings API, and a local model keeps catalog data inside our
infrastructure. Why fastembed over sentence-transformers: same models, no torch dependency,
image size ~100 MB instead of ~2 GB.
"""

from functools import lru_cache

from fastembed import TextEmbedding

from app.models import EMBEDDING_DIM

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class Embedder:
    def __init__(self, model_name: str = MODEL_NAME) -> None:
        self._model = TextEmbedding(model_name=model_name)

    def embed_passages(self, texts: list[str]) -> list[list[float]]:
        """Embed catalog texts. Vectors are L2-normalized, so cosine distance = 1 - dot."""
        vectors = [v.tolist() for v in self._model.passage_embed(texts)]
        assert all(len(v) == EMBEDDING_DIM for v in vectors)
        return vectors

    def embed_query(self, text: str) -> list[float]:
        return next(iter(self._model.query_embed([text]))).tolist()


@lru_cache
def get_embedder() -> Embedder:
    """One model instance per process. Loading takes seconds; do it once."""
    return Embedder()


def product_embed_text(name: str, description: str | None, category: str | None) -> str:
    """What the vector represents. SKU and price are excluded on purpose: they carry no
    semantic meaning and would only add noise. The keyword index (tsvector) covers SKUs."""
    parts = [name.strip()]
    if category:
        parts.append(category.strip())
    if description:
        parts.append(description.strip())
    return ". ".join(parts)
