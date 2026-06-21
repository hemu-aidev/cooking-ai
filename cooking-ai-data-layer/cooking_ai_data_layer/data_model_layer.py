"""
data_model_layer.py
--------------------
This is the ONE class the Application Layer needs to know about.
It hides recipe matching, video search, and local-model explanations
behind three simple methods: search(), ask_followup(), substitution().

Usage from your Flask/FastAPI app layer:

    from cooking_ai_data_layer import CookingDataModelLayer
    model_layer = CookingDataModelLayer()   # construct once at startup

    result = model_layer.search("margayta pizza")
    # -> matched recipe + ingredients + steps + youtube videos, typo and all
"""
import json
import os
from typing import Optional

from .embedding_search import RecipeSearchIndex
from .youtube_service import YouTubeService
from .local_llm_service import LocalLLMService
from . import config

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "recipes.json")


class CookingDataModelLayer:
    def __init__(
        self,
        recipes_path: str = DATA_PATH,
        youtube_api_key: Optional[str] = None,
        local_model_name: Optional[str] = None,
        embedding_model_name: Optional[str] = None,
    ):
        with open(recipes_path) as f:
            self.recipes = json.load(f)
        self.search_index = RecipeSearchIndex(self.recipes, model_name=embedding_model_name)
        self.youtube = YouTubeService(api_key=youtube_api_key)
        self.llm = LocalLLMService(model_name=local_model_name)

    def search(self, query: str, video_count: Optional[int] = None) -> dict:
        """Main entry point. One call -> recipe + ingredients + steps + videos."""
        match = self.search_index.best_match(query)
        if not match:
            return {
                "found": False,
                "query": query,
                "message": "No matching recipe found. Try a different dish name.",
            }
        recipe, confidence = match
        videos = self.youtube.search_videos(recipe["title"], max_results=video_count)
        return {
            "found": True,
            "query": query,
            "matched_title": recipe["title"],
            "confidence": round(confidence, 2),
            "recipe": recipe,
            "videos": videos,
        }

    def ask_followup(self, query: str, question: str) -> dict:
        """For the chat feature: 'can I make this without an oven?' etc."""
        match = self.search_index.best_match(query)
        if not match:
            return {"found": False, "answer": "I couldn't find that recipe to answer your question."}
        recipe, _ = match
        answer = self.llm.answer_followup(recipe, question)
        return {"found": True, "recipe_title": recipe["title"], "answer": answer}

    def substitution(self, query: str, ingredient: str) -> dict:
        match = self.search_index.best_match(query)
        if not match:
            return {"found": False, "answer": "Couldn't find that recipe."}
        recipe, _ = match
        answer = self.llm.suggest_substitution(recipe, ingredient)
        return {"found": True, "recipe_title": recipe["title"], "substitution": answer}
