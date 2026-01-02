# CLAUDE.md

Инструкции для Claude Code при работе с этим репозиторием.

## Обзор проекта

**Кухня Де Прусс** — сайт меню ресторана с админ-панелью. FastAPI + SQLAlchemy (async) + Jinja2.

| Компонент | Технология |
|-----------|------------|
| Backend | FastAPI, Python 3.11+ |
| Database | SQLite + aiosqlite (async) |
| ORM | SQLAlchemy 2.0 (async) |
| Templates | Jinja2 |
| Auth | JWT (httponly cookie, 24h) |
| Images | Pillow → WebP (4 размера) |
| CSS Build | Vite |

---

## Команды

```bash
# === Python ===
source .venv/bin/activate          # Активация venv
pip install -r requirements.txt    # Установка зависимостей
python scripts/init_db.py          # Инициализация БД
python scripts/quick_admin.py      # Создать admin/admin123
python scripts/import_menu.py      # Импорт меню из data/
python scripts/migrate_audit.py    # Миграция audit_logs

# === Сервер ===
uvicorn app.main:app --reload              # Dev сервер :8000
uvicorn app.main:app --reload --port 8080  # Другой порт

# === Frontend (Vite) ===
npm install      # Установка зависимостей
npm run build    # Сборка CSS
npm run watch    # Watch режим
```

---

## Структура проекта

```
app/
├── main.py                 # Точка входа, middleware, роутеры
├── config.py               # Настройки (pydantic-settings, .env)
├── database.py             # AsyncSession, engine
│
├── models/                 # SQLAlchemy модели
│   ├── category.py         # Category (name, slug, sort_order, is_active)
│   ├── dish.py             # Dish (price, weight, calories, 4 image sizes)
│   ├── admin_user.py       # AdminUser (bcrypt password)
│   └── audit_log.py        # AuditLog (action, entity, old/new JSON)
│
├── schemas/                # Pydantic схемы
│   ├── pagination.py       # PaginationParams, PaginatedResponse
│   ├── list_items.py       # DishListItem, CategoryListItem, etc.
│   └── requests.py         # BulkActionRequest, InlineEditRequest
│
├── services/               # Бизнес-логика
│   ├── auth.py             # JWT, bcrypt, authenticate_admin
│   ├── image_processor.py  # WebP конвертация, 4 размера
│   ├── rate_limiter.py     # Rate limiting для логина
│   ├── audit/              # Логирование действий
│   │   ├── service.py      # AuditService
│   │   └── helpers.py      # model_to_dict, compute_changes
│   └── data_exchange/      # Импорт/экспорт
│       ├── service.py      # DataExchangeService
│       ├── excel.py        # Excel функции
│       └── csv_handler.py  # CSV функции
│
├── api/
│   ├── menu.py             # Публичные роуты: /, /dish/{slug}
│   └── admin/              # Админ-панель /admin/*
│       ├── auth.py         # login, logout
│       ├── search.py       # Глобальный поиск
│       ├── dishes/         # CRUD блюд
│       │   ├── crud.py     # Формы, создание, редактирование
│       │   ├── api.py      # REST API, inline edit
│       │   ├── bulk.py     # Массовые операции, reorder
│       │   └── data_exchange.py  # Import/export
│       ├── categories/     # CRUD категорий (аналогично)
│       ├── dashboard/      # Статистика, activity feed
│       └── users/          # Управление админами
│
└── templates/
    ├── base.html           # Публичный layout
    ├── admin/base.html     # Админ layout
    ├── pages/              # index.html, dish.html
    └── admin/              # dashboard, dishes, categories, etc.

static/
├── css/
│   ├── admin/              # Админ стили (модульная структура)
│   │   ├── admin.css       # @import всех модулей
│   │   ├── base/           # variables, reset, scrollbar
│   │   ├── components/     # buttons, forms, tables, modals
│   │   ├── layouts/        # sidebar, header, main
│   │   ├── pages/          # dashboard, dishes, categories
│   │   └── utils/          # typography, filters, animations
│   ├── base/               # Публичные базовые стили
│   └── main/               # Публичные страницы
│       ├── animations/     # scroll-reveal, micro, keyframes
│       ├── components/     # hover-effects, category-filter
│       ├── pages/          # hero, dish-view
│       └── utils/          # responsive, helpers
│
├── js/
│   └── admin/              # Админ JS (IIFE модули)
│       ├── admin.js        # Инициализация
│       ├── api/client.js   # ApiClient для fetch
│       ├── components/     # toast, modal, sortable-table, bulk-actions
│       ├── services/       # validator, search
│       └── utils/          # shortcuts, table-nav, dashboard
│
└── uploads/dishes/{id}/    # Загруженные изображения
```

---

## Ключевые паттерны

### Async везде
```python
async with AsyncSession() as session:
    result = await session.execute(
        select(Dish).options(selectinload(Dish.category))
    )
```

### Slugs
```python
from slugify import slugify
dish.slug = slugify(dish.name, lowercase=True)  # "Борщ" → "borsch"
```

### Изображения
```python
# 4 размера WebP с timestamp для cache invalidation
processor = ImageProcessor()
paths = await processor.process_upload(file, dish_id)
# → thumbnail (100x100), small (200x200), medium (400x400), large (800x800)
```

### Аудит
```python
# Логирование изменений
old_data = model_to_dict(dish)  # До изменений
# ... изменения ...
await AuditService.log_update(session, admin, "dish", dish.id, old_data, new_data)
```

### JWT Auth
```python
# Cookie-based, httponly
response.set_cookie("access_token", token, httponly=True, max_age=86400)

# Проверка в роутах
admin = Depends(get_current_admin)
```

---

## Конвенции кода

### Python
- **Файлы ≤150 строк** — разбивать на модули
- **Async** — все DB операции через `await`
- **Type hints** — везде
- **Docstrings** — для публичных функций

### CSS (модульная структура)
```
static/css/{section}/
├── base/           # Переменные, reset
├── components/     # Кнопки, формы, карточки
├── layouts/        # Сетка, sidebar, header
├── pages/          # Страницы
├── utils/          # Хелперы, анимации
└── {section}.css   # @import всех модулей
```

### JavaScript (IIFE модули)
```javascript
(function() {
    'use strict';

    class ComponentName {
        constructor() { ... }
    }

    window.ComponentName = ComponentName;
})();
```

---

## База данных

**Путь**: `data/cafe.db`

### Модели

| Модель | Поля | Связи |
|--------|------|-------|
| Category | name, slug, sort_order, is_active | dishes (1:M) |
| Dish | name, slug, price, weight, calories, is_available, image_* | category (M:1) |
| AdminUser | username, password_hash, is_active | audit_logs (1:M) |
| AuditLog | action, entity_type, entity_id, old_data, new_data | admin_user (M:1) |

### Ограничения
- Категории нельзя удалить если есть блюда (RESTRICT)
- Slug уникален для dish и category

---

## API Endpoints

### Публичные
| Method | Path | Описание |
|--------|------|----------|
| GET | `/` | Главная страница меню |
| GET | `/dish/{slug}` | Страница блюда |
| GET | `/api/menu` | JSON меню |

### Админ (требует auth)
| Method | Path | Описание |
|--------|------|----------|
| GET/POST | `/admin/login` | Авторизация |
| GET | `/admin/` | Dashboard |
| CRUD | `/admin/dishes/*` | Управление блюдами |
| CRUD | `/admin/categories/*` | Управление категориями |
| GET | `/admin/api/search?q=` | Глобальный поиск |
| POST | `/admin/api/dishes/bulk` | Массовые операции |
| POST | `/admin/api/dishes/reorder` | Сортировка drag&drop |

---

## Переменные окружения (.env)

```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite+aiosqlite:///./data/cafe.db
DEBUG=true
```

---

## Частые задачи

### Добавить новое поле в модель
1. Обновить модель в `app/models/`
2. Добавить в схему `app/schemas/`
3. Обновить форму в шаблоне
4. Обновить CRUD в `app/api/admin/{entity}/crud.py`
5. Запустить `python scripts/init_db.py` (пересоздаст таблицы)

### Добавить новый компонент CSS
1. Создать `static/css/{section}/components/_name.css`
2. Добавить `@import` в `{section}.css`
3. Запустить `npm run build`

### Добавить новый JS модуль
1. Создать файл с IIFE в `static/js/admin/{folder}/`
2. Добавить `<script>` в `templates/admin/base.html`
3. Порядок важен — зависимости первыми

---

## Troubleshooting

| Проблема | Решение |
|----------|---------|
| `ModuleNotFoundError` | `source .venv/bin/activate` |
| CSS не обновляется | `npm run build` или Ctrl+Shift+R |
| Ошибка импорта в Python | Проверить `__init__.py` в модуле |
| 401 на /admin | Cookie истек, перелогиниться |
| Изображение не загружается | Проверить права на `static/uploads/` |
