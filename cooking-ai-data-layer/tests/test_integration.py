"""
test_integration.py
--------------------
Smoke tests for the installed package. These deliberately avoid
triggering real model downloads (no internet needed to run them) by
testing the deterministic parts: package structure, data integrity,
and the substitution knowledge-base path. Run with either:

    python tests/test_integration.py
    pytest tests/
"""
import json

from cooking_ai_data_layer import CookingDataModelLayer, config
from cooking_ai_data_layer.data_model_layer import DATA_PATH
from cooking_ai_data_layer.local_llm_service import LocalLLMService, SUBSTITUTIONS_PATH


def test_package_imports_cleanly():
    assert CookingDataModelLayer is not None
    assert config.EMBEDDING_MODEL_NAME == "all-MiniLM-L6-v2"


def test_recipe_data_is_valid():
    with open(DATA_PATH) as f:
        recipes = json.load(f)
    assert len(recipes) > 0
    for r in recipes:
        assert "title" in r and "ingredients" in r and "steps" in r
        assert len(r["ingredients"]) > 0
        assert len(r["steps"]) > 0


def test_substitution_knowledge_base_lookup():
    """Verifies the deterministic KB path works without needing the
    local generative model to be loaded."""
    svc = LocalLLMService.__new__(LocalLLMService)
    svc.model_name = config.LOCAL_LLM_MODEL_NAME
    svc._generator = None
    with open(SUBSTITUTIONS_PATH) as f:
        svc.substitution_kb = json.load(f)

    fake_recipe = {
        "title": "Margherita Pizza",
        "ingredients": [{"name": "mozzarella", "quantity": "200", "unit": "g"}],
        "steps": ["bake it"],
    }
    result = svc.suggest_substitution(fake_recipe, "mozzarella")
    assert "provolone" in result.lower()


def test_facade_exposes_integration_methods():
    for method in ("search", "ask_followup", "substitution"):
        assert hasattr(CookingDataModelLayer, method)


if __name__ == "__main__":
    test_package_imports_cleanly()
    test_recipe_data_is_valid()
    test_substitution_knowledge_base_lookup()
    test_facade_exposes_integration_methods()
    print("All smoke tests passed.")
