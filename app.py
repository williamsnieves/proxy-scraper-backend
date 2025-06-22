#!/usr/bin/env python3
"""
Default app.py entry point for Render.
Render automatically looks for this file.
"""

from proxy_scraper import app

if __name__ == "__main__":
    import os
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False) 