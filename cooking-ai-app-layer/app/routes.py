"""
app/routes.py
--------------
Three endpoints, each a thin wrapper around one CookingDataModelLayer
method. This is intentional: validation and HTTP concerns live here,
recipe/search/model logic stays entirely in the data layer.
"""
from flask import Blueprint, request, jsonify, current_app

bp = Blueprint("api", __name__)


def get_model_layer():
    return current_app.extensions["model_layer"]


@bp.route("/search", methods=["GET"])
def search():
    """GET /api/search?q=margayta+pizza&videos=4"""
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Missing required query param 'q'"}), 400

    video_count = request.args.get("videos", type=int)
    result = get_model_layer().search(query, video_count=video_count)
    status = 200 if result.get("found") else 404
    return jsonify(result), status


@bp.route("/ask", methods=["POST"])
def ask():
    """POST /api/ask  {"query": "margherita pizza", "question": "no oven?"}"""
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    question = (data.get("question") or "").strip()
    if not query or not question:
        return jsonify({"error": "Both 'query' and 'question' are required"}), 400

    result = get_model_layer().ask_followup(query, question)
    status = 200 if result.get("found") else 404
    return jsonify(result), status


@bp.route("/substitute", methods=["POST"])
def substitute():
    """POST /api/substitute  {"query": "margherita pizza", "ingredient": "mozzarella"}"""
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    ingredient = (data.get("ingredient") or "").strip()
    if not query or not ingredient:
        return jsonify({"error": "Both 'query' and 'ingredient' are required"}), 400

    result = get_model_layer().substitution(query, ingredient)
    status = 200 if result.get("found") else 404
    return jsonify(result), status
