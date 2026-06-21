"""
test_routes.py
---------------
Tests the Application Layer in isolation by injecting a fake model
layer with the same interface as CookingDataModelLayer. This proves
the Flask wiring, validation, and status codes are correct without
needing the real embedding/LLM models downloaded — useful in CI or
any environment without internet access to Hugging Face.

Run with:  python -m unittest tests/test_routes.py
"""
import unittest
from app import create_app


class FakeModelLayer:
    """Same method signatures as CookingDataModelLayer, fake data."""

    def search(self, query, video_count=None):
        if "pizza" in query.lower():
            return {
                "found": True,
                "query": query,
                "matched_title": "Margherita Pizza",
                "confidence": 0.91,
                "recipe": {"title": "Margherita Pizza", "ingredients": [], "steps": []},
                "videos": [],
            }
        return {"found": False, "query": query, "message": "No matching recipe found."}

    def ask_followup(self, query, question):
        return {
            "found": True,
            "recipe_title": "Margherita Pizza",
            "answer": "Use a heavy baking sheet preheated as hot as your oven allows.",
        }

    def substitution(self, query, ingredient):
        return {
            "found": True,
            "recipe_title": "Margherita Pizza",
            "substitution": "Provolone melts similarly with a sharper flavor.",
        }


class RoutesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(model_layer=FakeModelLayer())
        self.app.testing = True
        self.client = self.app.test_client()

    def test_health(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)

    def test_search_missing_query_returns_400(self):
        resp = self.client.get("/api/search")
        self.assertEqual(resp.status_code, 400)

    def test_search_found_returns_200(self):
        resp = self.client.get("/api/search?q=margayta+pizza")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["matched_title"], "Margherita Pizza")

    def test_search_not_found_returns_404(self):
        resp = self.client.get("/api/search?q=something+random")
        self.assertEqual(resp.status_code, 404)

    def test_ask_missing_fields_returns_400(self):
        resp = self.client.post("/api/ask", json={"query": "pizza"})
        self.assertEqual(resp.status_code, 400)

    def test_ask_ok_returns_200(self):
        resp = self.client.post(
            "/api/ask", json={"query": "pizza", "question": "no oven, what do I do?"}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("answer", resp.get_json())

    def test_substitute_ok_returns_200(self):
        resp = self.client.post(
            "/api/substitute", json={"query": "pizza", "ingredient": "mozzarella"}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("substitution", resp.get_json())


if __name__ == "__main__":
    unittest.main()
