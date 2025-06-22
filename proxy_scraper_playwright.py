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
import json
from urllib.parse import urlparse
from playwright.async_api import async_playwright
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Permitir requests desde cualquier origen

class PlaywrightProxyScraper:
    """Scraper avanzado que usa Playwright para manejar JavaScript."""
    
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        self.playwright = None
        self.browser = None
    
    async def initialize_playwright(self):
        """Inicializar Playwright si no está ya inicializado."""
        if self.playwright is None:
            logger.info("🎭 Initializing Playwright...")
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu'
                ]
            )
            logger.info("✅ Playwright initialized successfully")
    
    async def cleanup_playwright(self):
        """Limpiar recursos de Playwright."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    def get_natural_headers(self, url: str) -> dict:
        """Headers que parecen venir de un navegador real."""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        headers = {
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
    
    async def fetch_with_playwright(self, url: str) -> dict:
        """Fetch URL usando Playwright (para sitios con JavaScript)."""
        try:
            await self.initialize_playwright()
            
            logger.info(f"🎭 Using Playwright for {url}")
            
            # Crear contexto del navegador
            context = await self.browser.new_context(
                user_agent=random.choice(self.user_agents),
                viewport={'width': 1920, 'height': 1080},
                extra_http_headers=self.get_natural_headers(url)
            )
            
            # Crear página
            page = await context.new_page()
            
            # Configurar timeouts
            page.set_default_timeout(30000)  # 30 segundos
            
            # Navegar a la página
            response = await page.goto(url, wait_until='domcontentloaded')
            
            # Esperar un poco para que se cargue el JavaScript
            await page.wait_for_timeout(3000)
            
            # Obtener el contenido HTML final
            content = await page.content()
            
            # Obtener información adicional
            title = await page.title()
            final_url = page.url
            
            await context.close()
            
            return {
                'success': True,
                'status_code': response.status if response else 200,
                'content': content,
                'title': title,
                'url': final_url,
                'method': 'playwright'
            }
        
        except Exception as e:
            logger.error(f"❌ Playwright error for {url}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'status_code': 0,
                'method': 'playwright'
            }
    
    async def fetch_with_aiohttp(self, url: str) -> dict:
        """Fetch URL usando aiohttp (para sitios simples)."""
        try:
            logger.info(f"🌐 Using aiohttp for {url}")
            
            timeout = aiohttp.ClientTimeout(total=30)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                headers = self.get_natural_headers(url)
                headers['User-Agent'] = random.choice(self.user_agents)
                
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
                        'url': str(response.url),
                        'method': 'aiohttp'
                    }
        
        except Exception as e:
            logger.error(f"❌ aiohttp error for {url}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'status_code': 0,
                'method': 'aiohttp'
            }
    
    def needs_playwright(self, url: str) -> bool:
        """Determinar si una URL necesita Playwright."""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Sitios que sabemos que requieren JavaScript
        js_required_domains = [
            'etsy.com',
            'amazon.com',
            'ebay.com',
            'shopify.com',
            'bigcommerce.com'
        ]
        
        return any(js_domain in domain for js_domain in js_required_domains)
    
    async def fetch_url(self, url: str, force_playwright: bool = False) -> dict:
        """
        Fetch URL con la estrategia más apropiada.
        
        Args:
            url: URL a scrapear
            force_playwright: Forzar uso de Playwright
        """
        try:
            # Decidir qué método usar
            if force_playwright or self.needs_playwright(url):
                result = await self.fetch_with_playwright(url)
                
                # Si Playwright falla, intentar con aiohttp como fallback
                if not result['success']:
                    logger.info(f"🔄 Playwright failed, trying aiohttp fallback for {url}")
                    fallback_result = await self.fetch_with_aiohttp(url)
                    if fallback_result['success']:
                        return fallback_result
                
                return result
            else:
                result = await self.fetch_with_aiohttp(url)
                
                # Si aiohttp falla o detectamos bloqueo, intentar con Playwright
                if not result['success'] or self._is_blocked_content(result.get('content', '')):
                    logger.info(f"🔄 aiohttp blocked/failed, trying Playwright for {url}")
                    return await self.fetch_with_playwright(url)
                
                return result
        
        except Exception as e:
            logger.error(f"❌ General error for {url}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'status_code': 0,
                'method': 'error'
            }
    
    def _is_blocked_content(self, content: str) -> bool:
        """Detectar si el contenido está bloqueado."""
        if not content:
            return True
        
        blocking_indicators = [
            'Please enable JS and disable any ad blocker',
            'captcha-delivery.com',
            'cloudflare',
            'just a moment',
            'checking your browser',
            'ddos protection by cloudflare',
            'access denied',
            'blocked'
        ]
        
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in blocking_indicators)

# Instancia global del scraper
proxy_scraper = PlaywrightProxyScraper()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy', 
        'service': 'proxy-scraper-playwright',
        'features': ['aiohttp', 'playwright', 'javascript-support']
    })

@app.route('/scrape', methods=['POST'])
def scrape_url():
    """
    Scrape a URL and return the content.
    
    Body: {
        "url": "https://example.com",
        "force_playwright": false  // opcional
    }
    """
    data = request.get_json()
    
    if not data or 'url' not in data:
        return jsonify({'error': 'URL is required'}), 400
    
    url = data['url']
    force_playwright = data.get('force_playwright', False)
    
    # Ejecutar el scraping asíncrono
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(proxy_scraper.fetch_url(url, force_playwright))
        return jsonify(result)
    finally:
        loop.close()

@app.route('/batch-scrape', methods=['POST'])
def batch_scrape():
    """
    Scrape multiple URLs.
    
    Body: {
        "urls": ["https://example1.com", "https://example2.com"],
        "force_playwright": false  // opcional
    }
    """
    data = request.get_json()
    
    if not data or 'urls' not in data:
        return jsonify({'error': 'URLs array is required'}), 400
    
    urls = data['urls']
    force_playwright = data.get('force_playwright', False)
    
    if not isinstance(urls, list) or len(urls) == 0:
        return jsonify({'error': 'URLs must be a non-empty array'}), 400
    
    if len(urls) > 5:  # Límite reducido para Playwright
        return jsonify({'error': 'Maximum 5 URLs allowed for batch scraping'}), 400
    
    # Scraping en batch
    async def fetch_all():
        tasks = [proxy_scraper.fetch_url(url, force_playwright) for url in urls]
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

# Cleanup al cerrar la aplicación
import atexit

def cleanup():
    """Limpiar recursos al cerrar."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(proxy_scraper.cleanup_playwright())
        loop.close()
    except:
        pass

atexit.register(cleanup)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8080))
    
    print("🚀 Starting Playwright Proxy Scraper Backend")
    print(f"📡 Running on port: {port}")
    print("🎭 Features: Playwright + aiohttp")
    print("🔧 Endpoints:")
    print("   GET  /health")
    print("   POST /scrape")
    print("   POST /batch-scrape")
    print("")
    
    app.run(host='0.0.0.0', port=port, debug=False) 