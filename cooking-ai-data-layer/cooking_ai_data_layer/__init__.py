"""
cooking_ai_data_layer
======================
Data/Model layer for the Cooking AI product: recipe search (pretrained
embedding model + fuzzy match), explanations (local pretrained LLM, no
hosted API), and relevant video lookup (YouTube Data API).

Quick start:

    from cooking_ai_data_layer import CookingDataModelLayer

    model_layer = CookingDataModelLayer()       # build once, reuse everywhere
    result = model_layer.search("margayta pizza")
    answer = model_layer.ask_followup("margherita pizza", "no pizza stone, what do I do?")
    sub = model_layer.substitution("margherita pizza", "mozzarella")

That's the entire integration surface the Application Layer needs.
"""
from .data_model_layer import CookingDataModelLayer
from . import config

__version__ = "0.1.0"
__all__ = ["CookingDataModelLayer", "config"]
