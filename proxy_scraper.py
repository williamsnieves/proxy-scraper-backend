#!/usr/bin/env python3
"""
Proxy Backend con Playwright para Web Scraping
Maneja sitios con JavaScript, Cloudflare, y otras protecciones avanzadas.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import aiohttp
import random
from urllib.parse import urlparse
from playwright.async_api import async_playwright
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Permitir requests desde cualquier origen

class ProxyScraper:
    """Scraper que actúa como proxy intermedio."""
    
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
    
    def get_natural_headers(self, url: str) -> dict:
        """Headers que parecen venir de un navegador real."""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1'
        }
        
        # Simular navegación natural desde Google
        if 'etsy.com' in domain:
            headers.update({
                'Referer': 'https://www.google.com/',
                'Sec-Fetch-Site': 'cross-site'
            })
        elif 'gumroad.com' in domain:
            headers.update({
                'Referer': 'https://www.google.com/',
                'Sec-Fetch-Site': 'cross-site'
            })
        else:
            headers['Sec-Fetch-Site'] = 'none'
        
        return headers
    
    async def fetch_url(self, url: str) -> dict:
        """Fetch URL content and return structured response."""
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                headers = self.get_natural_headers(url)
                
                async with session.get(
                    url, 
                    headers=headers,
                    allow_redirects=True,
                    ssl=False
                ) as response:
                    
                    content = await response.text()
                    
                    return {
                        'success': True,
                        'status_code': response.status,
                        'content': content,
                        'headers': dict(response.headers),
                        'url': str(response.url)
                    }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': 0
            }

proxy_scraper = ProxyScraper()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'proxy-scraper'})

@app.route('/scrape', methods=['POST'])
def scrape_url():
    """
    Scrape a URL and return the content.
    
    Body: {"url": "https://example.com"}
    """
    data = request.get_json()
    
    if not data or 'url' not in data:
        return jsonify({'error': 'URL is required'}), 400
    
    url = data['url']
    
    # Ejecutar el scraping asíncrono
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(proxy_scraper.fetch_url(url))
        return jsonify(result)
    finally:
        loop.close()

@app.route('/batch-scrape', methods=['POST'])
def batch_scrape():
    """
    Scrape multiple URLs.
    
    Body: {"urls": ["https://example1.com", "https://example2.com"]}
    """
    data = request.get_json()
    
    if not data or 'urls' not in data:
        return jsonify({'error': 'URLs array is required'}), 400
    
    urls = data['urls']
    
    if not isinstance(urls, list) or len(urls) == 0:
        return jsonify({'error': 'URLs must be a non-empty array'}), 400
    
    if len(urls) > 10:  # Límite de seguridad
        return jsonify({'error': 'Maximum 10 URLs allowed'}), 400
    
    # Scraping en batch
    async def fetch_all():
        tasks = [proxy_scraper.fetch_url(url) for url in urls]
        return await asyncio.gather(*tasks)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        results = loop.run_until_complete(fetch_all())
        return jsonify({
            'results': dict(zip(urls, results)),
            'total': len(urls)
        })
    finally:
        loop.close()

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8080))
    
    print("🚀 Starting Proxy Scraper Backend")
    print(f"📡 Running on port: {port}")
    print("🔧 Endpoints:")
    print("   GET  /health")
    print("   POST /scrape")
    print("   POST /batch-scrape")
    print("")
    
    app.run(host='0.0.0.0', port=port, debug=False) 