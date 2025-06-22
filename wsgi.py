#!/usr/bin/env python3
"""
WSGI entry point for Render deployment.
This file allows Render to find our Flask app easily.
"""

from proxy_scraper import app

if __name__ == "__main__":
    app.run() 