# 🌐 Proxy Scraper Backend

Backend proxy service para evitar problemas de origen localhost en web scraping.

## 🚀 Deployed on Railway

Este servicio actúa como proxy intermedio para requests de scraping, evitando que sitios como Etsy detecten el origen localhost.

## 📡 Endpoints

### GET /health
Verificar estado del servicio
```bash
curl https://tu-app.railway.app/health
```

### POST /scrape
Scrapear una URL individual
```bash
curl -X POST https://tu-app.railway.app/scrape \
  -H "Content-Type: application/json" \
  -d '{"url": "https://etsy.com/listing/123"}'
```

### POST /batch-scrape
Scrapear múltiples URLs
```bash
curl -X POST https://tu-app.railway.app/batch-scrape \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://etsy.com/listing/123", "https://gumroad.com/product/456"]}'
```

## 🔧 Configuración

- **Puerto**: Configurado automáticamente por Railway ($PORT)
- **CORS**: Habilitado para todas las origins
- **Timeout**: 30s para requests individuales, 120s para batch

## 📊 Arquitectura

```
[Cliente] → [Railway Proxy] → [Sitio Web]
             ↑
        Origen limpio
        Sin localhost
``` 