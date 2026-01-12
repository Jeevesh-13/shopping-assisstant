"""
Vercel serverless function entrypoint.
This file exports the FastAPI app for Vercel's Python runtime.
"""
from app.main import app

# Vercel expects the app to be exported at module level
__all__ = ["app"]
