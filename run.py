"""
Run Script
==========
Entry point for the Flask application.

Usage:
    python3 run.py          # Starts the dev server
    python3 -m flask db ... # Database commands
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)