"""
app/__init__.py
----------------
Application Layer entry point. Responsible for: receiving HTTP requests
from the Presentation Layer, validating input, calling the Data/Model
Layer, and shaping consistent JSON responses. It owns NO recipe logic,
search logic, or model logic itself — all of that lives in
cooking_ai_data_layer and is only ever called through its facade.
"""
from flask import Flask
from cooking_ai_data_layer import CookingDataModelLayer

try:
    from flask_cors import CORS
except ImportError:
    CORS = None  # falls back to no CORS; install flask-cors for a browser frontend


def create_app(model_layer=None):
    """
    model_layer: optional pre-built CookingDataModelLayer (or compatible
    stub). Pass a fake here in tests so you're not waiting on real model
    downloads just to test routing/validation. In production, leave it
    None and the real data layer is built once at startup.
    """
    app = Flask(__name__)

    if CORS:
        CORS(app)  # lets a frontend on a different origin call this API
    else:
        app.logger.warning("flask-cors not installed — CORS is disabled. "
                            "Run: pip install flask-cors")

    # Built ONCE here, reused for every request via app.extensions.
    # This is the entire connection point to the Data/Model Layer.
    app.extensions["model_layer"] = model_layer or CookingDataModelLayer()

    from .routes import bp as api_bp
    app.register_blueprint(api_bp, url_prefix="/api")

    from .errors import register_error_handlers
    register_error_handlers(app)

    @app.route("/health")
    def health():
        return {"status": "ok"}

    return app
