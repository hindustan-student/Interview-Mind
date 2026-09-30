import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set Vercel environment flags
os.environ.setdefault("FLASK_ENV", "production")
os.environ.setdefault("VERCEL", "1")

from app import create_app

# WSGI application callable for Vercel Serverless
app = create_app("production")

if __name__ == "__main__":
    app.run()
