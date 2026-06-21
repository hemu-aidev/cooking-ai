"""
app/errors.py
--------------
Ensures every failure — bad input, missing recipe, or an unexpected
exception bubbling up from the data layer — returns a clean JSON error
instead of a raw stack trace or an HTML error page.
"""
from flask import jsonify


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(Exception)
    def handle_unexpected(e):
        # Covers things like the local model not being loaded yet,
        # YouTube quota errors that weren't caught downstream, etc.
        app.logger.exception("Unhandled exception in request")
        return jsonify({"error": "Something went wrong processing your request"}), 500
