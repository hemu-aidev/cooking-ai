"""
local_llm_service.py
---------------------
Generates recipe explanations and substitution suggestions using an
OPEN-SOURCE PRETRAINED MODEL THAT RUNS LOCALLY, in your own process.
No calls to Claude, ChatGPT, Gemini, or any other hosted model API —
the model weights are downloaded once from Hugging Face and then run
entirely on your own CPU/GPU.

Why Flan-T5 (default): instruction-tuned, Apache-2.0 licensed for
commercial use, and the 'base' checkpoint (248M params) is small enough
to run on a normal CPU with no GPU required — a realistic self-hosted
choice. Override via config.LOCAL_LLM_MODEL_NAME (env var
LOCAL_LLM_MODEL_NAME) — e.g. "google/flan-t5-large" if you have a GPU
and want noticeably better answer quality.

Design choice (why a knowledge base AND a model):
A generative model alone can hallucinate quantities or facts. So for
substitutions — where wrong answers actually ruin a dish — we check our
own curated data first (data/substitutions.json) and only fall back to
the model for ingredients we haven't catalogued yet. This is the same
"retrieval before generation" pattern real production systems use.
"""
import os
import json
from typing import Optional

from . import config

try:
    from transformers import pipeline
except ImportError:
    pipeline = None

SUBSTITUTIONS_PATH = os.path.join(os.path.dirname(__file__), "data", "substitutions.json")


class LocalLLMService:
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or config.LOCAL_LLM_MODEL_NAME
        self._generator = None
        with open(SUBSTITUTIONS_PATH) as f:
            self.substitution_kb = json.load(f)

    @property
    def generator(self):
        """Lazy-loaded: model weights only load into memory the first time
        they're actually needed, not at import time or app startup."""
        if self._generator is None:
            if pipeline is None:
                raise RuntimeError(
                    "Run: pip install transformers torch sentencepiece"
                )
            self._generator = pipeline("text2text-generation", model=self.model_name)
        return self._generator

    @staticmethod
    def _build_recipe_context(recipe: dict) -> str:
        ingredients = ", ".join(i["name"] for i in recipe["ingredients"])
        steps = " ".join(recipe["steps"])
        return f"Recipe: {recipe['title']}. Ingredients: {ingredients}. Steps: {steps}"

    def answer_followup(self, recipe: dict, question: str) -> str:
        context = self._build_recipe_context(recipe)
        prompt = (
            "Answer the cooking question using only the recipe context below.\n"
            f"Context: {context}\nQuestion: {question}\nAnswer:"
        )
        try:
            result = self.generator(prompt, max_new_tokens=120, do_sample=False)
            return result[0]["generated_text"].strip()
        except Exception as e:
            return f"Local model unavailable right now ({e})."

    def suggest_substitution(self, recipe: dict, ingredient: str) -> str:
        key = ingredient.lower().strip()

        # 1. Our own curated data first — deterministic and reliable.
        if key in self.substitution_kb:
            options = self.substitution_kb[key]
            lines = [f"- {o['substitute']}: {o['note']}" for o in options]
            return f"Substitutes for {ingredient}:\n" + "\n".join(lines)

        # 2. Fall back to the local generative model, grounded in the recipe.
        context = self._build_recipe_context(recipe)
        prompt = (
            f"Context: {context}\nSuggest one substitute for '{ingredient}' "
            "and explain in one sentence how it changes taste or texture.\nAnswer:"
        )
        try:
            result = self.generator(prompt, max_new_tokens=80, do_sample=False)
            return result[0]["generated_text"].strip()
        except Exception as e:
            return f"No substitution data available for '{ingredient}' ({e})."
