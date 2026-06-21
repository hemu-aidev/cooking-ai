"""
embedding_search.py
--------------------
Recipe search powered by a pretrained model.

Why hybrid (fuzzy + semantic) instead of just one:
- Fuzzy string matching (rapidfuzz) catches typos: "margayta pizza" -> "Margherita Pizza"
- Semantic embeddings (sentence-transformers) catch paraphrasing/intent:
  "cheesy italian flatbread" -> "Margherita Pizza" even with zero overlapping words
A real product needs both; relying on only one gives a worse search experience.

Model used by default: all-MiniLM-L6-v2 (sentence-transformers)
- Pretrained on 1B+ sentence pairs, 22M params, runs fast on CPU
- Industry-standard choice for lightweight semantic search / retrieval
- Override via config.EMBEDDING_MODEL_NAME (env var EMBEDDING_MODEL_NAME)
"""
from typing import List, Tuple, Optional

import numpy as np

from . import config

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

try:
    from rapidfuzz import fuzz
except ImportError:
    fuzz = None


class RecipeSearchIndex:
    def __init__(self, recipes: List[dict], model_name: Optional[str] = None):
        self.recipes = recipes
        self.model_name = model_name or config.EMBEDDING_MODEL_NAME
        self._model = None
        self._embeddings: Optional[np.ndarray] = None
        self._build_index()

    @property
    def model(self):
        if self._model is None:
            if SentenceTransformer is None:
                raise RuntimeError(
                    "sentence-transformers not installed. Run: "
                    "pip install sentence-transformers"
                )
            self._model = SentenceTransformer(self.model_name)
        return self._model

    @staticmethod
    def _searchable_text(recipe: dict) -> str:
        tags = " ".join(recipe.get("tags", []))
        ingredient_names = " ".join(i["name"] for i in recipe.get("ingredients", []))
        return f"{recipe['title']} {tags} {ingredient_names}"

    def _build_index(self):
        """Embed every recipe once at construction time. In production with
        thousands of recipes, swap the in-memory matrix below for a FAISS or
        Pinecone/Weaviate vector index — the search() interface stays the same,
        so nothing in the layers above this one would need to change."""
        texts = [self._searchable_text(r) for r in self.recipes]
        self._embeddings = self.model.encode(texts, normalize_embeddings=True)

    def _semantic_scores(self, query: str) -> np.ndarray:
        q_emb = self.model.encode([query], normalize_embeddings=True)[0]
        return self._embeddings @ q_emb  # cosine similarity (vectors are normalized)

    def _fuzzy_scores(self, query: str) -> np.ndarray:
        if fuzz is None:
            return np.zeros(len(self.recipes))
        return np.array([
            fuzz.WRatio(query.lower(), r["title"].lower()) / 100.0
            for r in self.recipes
        ])

    def search(self, query: str, top_k: int = 1) -> List[Tuple[dict, float]]:
        semantic = self._semantic_scores(query)
        fuzzy = self._fuzzy_scores(query)
        combined = 0.5 * semantic + 0.5 * fuzzy
        ranked_idx = np.argsort(-combined)[:top_k]
        return [(self.recipes[i], float(combined[i])) for i in ranked_idx]

    def best_match(
        self, query: str, min_confidence: Optional[float] = None
    ) -> Optional[Tuple[dict, float]]:
        threshold = min_confidence if min_confidence is not None else config.SEARCH_MIN_CONFIDENCE
        results = self.search(query, top_k=1)
        if not results:
            return None
        recipe, score = results[0]
        return (recipe, score) if score >= threshold else None
