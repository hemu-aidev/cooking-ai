"""
run.py
------
Local dev entrypoint:  python run.py
Production entrypoint (via gunicorn):  gunicorn --preload run:app
"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
