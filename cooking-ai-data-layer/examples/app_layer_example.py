"""
app_layer_example.py
---------------------
Illustrates how the Application Layer (your existing Flask app) wires up
to the Data/Model Layer once it's installed as a package:

    pip install -e /path/to/cooking-ai-data-layer

After that, this import works from ANY project on the same machine/venv —
the data layer no longer needs to live next to your app.py.
"""
from flask import Flask, request, jsonify
from cooking_ai_data_layer import CookingDataModelLayer

app = Flask(__name__)

# Built once at startup (loads the embedding model + recipe data into memory),
# then reused across every request — do NOT recreate this per-request.
model_layer = CookingDataModelLayer()


@app.route("/api/search", methods=["GET"])
def search_recipe():
    query = request.args.get("q", "")
    return jsonify(model_layer.search(query))


@app.route("/api/ask", methods=["POST"])
def ask():
    data = request.get_json()
    return jsonify(model_layer.ask_followup(data["query"], data["question"]))


@app.route("/api/substitute", methods=["POST"])
def substitute():
    data = request.get_json()
    return jsonify(model_layer.substitution(data["query"], data["ingredient"]))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
