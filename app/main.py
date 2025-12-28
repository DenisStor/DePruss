from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse, Response
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime

from app.config import get_settings
from app.database import init_db, async_session
from app.api.menu import router as menu_router
from app.api.admin.router import router as admin_router
from app.models.dish import Dish
from sqlalchemy import select

settings = get_settings()


# Cache headers middleware
class CacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        path = request.url.path

        # Статические файлы - долгий кеш
        if path.startswith("/static/"):
            if path.endswith((".css", ".js")):
                response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
            elif path.endswith((".webp", ".jpg", ".png")):
                response.headers["Cache-Control"] = "public, max-age=2592000"

        # API - короткий кеш с revalidate
        elif path.startswith("/api/"):
            response.headers["Cache-Control"] = "public, max-age=300, stale-while-revalidate=86400"

        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
    docs_url="/api/docs" if settings.debug else None,
    redoc_url=None
)

# Middleware (порядок важен!)
app.add_middleware(GZipMiddleware, minimum_size=500)
app.add_middleware(CacheMiddleware)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Routers
app.include_router(menu_router)
app.include_router(admin_router)


# Error handlers
@app.exception_handler(401)
async def unauthorized_handler(request: Request, exc):
    if request.url.path.startswith("/admin"):
        return RedirectResponse(url="/admin/login", status_code=302)
    return HTMLResponse(content="Unauthorized", status_code=401)


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    # Для API запросов возвращаем JSON
    if request.url.path.startswith("/api/"):
        return HTMLResponse(
            content='{"detail": "Not found"}',
            status_code=404,
            media_type="application/json"
        )
    # Читаем HTML шаблон
    with open("app/templates/errors/404.html", "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content=content, status_code=404)


# robots.txt
@app.get("/robots.txt", response_class=PlainTextResponse)
async def robots():
    return """User-agent: *
Allow: /
Disallow: /admin/
Disallow: /api/

Sitemap: https://depruss.ru/sitemap.xml
"""


# sitemap.xml
@app.get("/sitemap.xml")
async def sitemap():
    now = datetime.now().strftime("%Y-%m-%d")

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

    # Главная страница
    xml += f'''  <url>
    <loc>https://depruss.ru/</loc>
    <lastmod>{now}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>\n'''

    # Страницы блюд
    async with async_session() as session:
        result = await session.execute(
            select(Dish.slug, Dish.updated_at).where(Dish.is_available == True)
        )
        dishes = result.all()

        for dish_slug, updated_at in dishes:
            lastmod = updated_at.strftime("%Y-%m-%d") if updated_at else now
            xml += f'''  <url>
    <loc>https://depruss.ru/dish/{dish_slug}</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>\n'''

    xml += '</urlset>'

    return Response(content=xml, media_type="application/xml")
