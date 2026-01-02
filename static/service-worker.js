/**
 * Service Worker для Кухня Де Прусс
 * Кеширование и offline поддержка
 */

const CACHE_VERSION = 'v1';
const STATIC_CACHE = `static-${CACHE_VERSION}`;
const IMAGES_CACHE = `images-${CACHE_VERSION}`;
const PAGES_CACHE = `pages-${CACHE_VERSION}`;
const API_CACHE = `api-${CACHE_VERSION}`;

// Критические ресурсы для предзагрузки
const PRECACHE_URLS = [
    '/',
    '/static/css/base/base.css',
    '/static/css/main/main.css',
    '/static/js/network-adapter.js',
    '/static/js/progressive-image.js',
    '/static/js/lazy-load.js',
    '/offline'
];

// Установка Service Worker
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then((cache) => {
                console.log('[SW] Precaching static assets');
                return cache.addAll(PRECACHE_URLS);
            })
            .then(() => self.skipWaiting())
    );
});

// Активация и очистка старых кешей
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames
                        .filter((name) => {
                            // Удаляем кеши со старой версией
                            return name.startsWith('static-') ||
                                   name.startsWith('images-') ||
                                   name.startsWith('pages-') ||
                                   name.startsWith('api-');
                        })
                        .filter((name) => {
                            return name !== STATIC_CACHE &&
                                   name !== IMAGES_CACHE &&
                                   name !== PAGES_CACHE &&
                                   name !== API_CACHE;
                        })
                        .map((name) => {
                            console.log('[SW] Deleting old cache:', name);
                            return caches.delete(name);
                        })
                );
            })
            .then(() => self.clients.claim())
    );
});

// Обработка запросов
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // Пропускаем non-GET запросы
    if (event.request.method !== 'GET') {
        return;
    }

    // Пропускаем admin и auth
    if (url.pathname.startsWith('/admin')) {
        return;
    }

    // Определяем стратегию по типу ресурса
    if (isStaticAsset(url)) {
        event.respondWith(cacheFirst(event.request, STATIC_CACHE));
    } else if (isImage(url)) {
        event.respondWith(cacheFirstWithRefresh(event.request, IMAGES_CACHE));
    } else if (isApiRequest(url)) {
        event.respondWith(staleWhileRevalidate(event.request, API_CACHE));
    } else if (isPageRequest(event.request)) {
        event.respondWith(networkFirstWithFallback(event.request, PAGES_CACHE));
    }
});

/**
 * Cache First - для статических ресурсов
 */
async function cacheFirst(request, cacheName) {
    const cached = await caches.match(request);
    if (cached) {
        return cached;
    }

    try {
        const response = await fetch(request);
        if (response.ok) {
            const cache = await caches.open(cacheName);
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        console.warn('[SW] Cache first failed:', error);
        throw error;
    }
}

/**
 * Cache First с фоновым обновлением - для изображений
 */
async function cacheFirstWithRefresh(request, cacheName) {
    const cached = await caches.match(request);

    // Фоновое обновление
    const fetchPromise = fetch(request)
        .then((response) => {
            if (response.ok) {
                caches.open(cacheName).then((cache) => {
                    cache.put(request, response.clone());
                });
            }
            return response;
        })
        .catch(() => null);

    // Возвращаем кеш сразу, если есть
    if (cached) {
        return cached;
    }

    // Иначе ждём сеть
    const response = await fetchPromise;
    if (response) {
        return response;
    }

    // Fallback на placeholder
    return caches.match('/static/images/placeholder.webp');
}

/**
 * Stale While Revalidate - для API
 */
async function staleWhileRevalidate(request, cacheName) {
    const cache = await caches.open(cacheName);
    const cached = await cache.match(request);

    // Обновляем кеш в фоне
    const fetchPromise = fetch(request)
        .then((response) => {
            if (response.ok) {
                cache.put(request, response.clone());
            }
            return response;
        })
        .catch(() => null);

    // Возвращаем кеш если есть, иначе ждём сеть
    return cached || fetchPromise;
}

/**
 * Network First с fallback - для страниц
 */
async function networkFirstWithFallback(request, cacheName) {
    try {
        const response = await fetch(request);

        if (response.ok) {
            const cache = await caches.open(cacheName);
            cache.put(request, response.clone());
        }

        return response;
    } catch (error) {
        // Пробуем из кеша
        const cached = await caches.match(request);
        if (cached) {
            return cached;
        }

        // Offline страница
        const offlinePage = await caches.match('/offline');
        if (offlinePage) {
            return offlinePage;
        }

        // Генерируем базовый offline ответ
        return new Response(
            '<html><body><h1>Нет подключения</h1><p>Проверьте интернет-соединение</p></body></html>',
            {
                headers: { 'Content-Type': 'text/html; charset=utf-8' },
                status: 503
            }
        );
    }
}

/**
 * Проверки типов ресурсов
 */
function isStaticAsset(url) {
    return url.pathname.match(/\.(css|js|woff2?|ttf|eot)$/i) ||
           url.pathname.startsWith('/static/css/') ||
           url.pathname.startsWith('/static/js/');
}

function isImage(url) {
    return url.pathname.match(/\.(webp|avif|jpg|jpeg|png|gif|svg|ico)$/i) ||
           url.pathname.startsWith('/static/uploads/') ||
           url.pathname.startsWith('/static/images/');
}

function isApiRequest(url) {
    return url.pathname.startsWith('/api/');
}

function isPageRequest(request) {
    return request.mode === 'navigate' ||
           request.headers.get('Accept')?.includes('text/html');
}

// Сообщение о новой версии
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});
