/**
 * Service Worker Registration
 * Регистрирует SW и обрабатывает обновления
 */

(function() {
    'use strict';

    // Проверяем поддержку Service Worker
    if (!('serviceWorker' in navigator)) {
        console.log('[SW] Service Worker not supported');
        return;
    }

    // Регистрируем после загрузки страницы
    window.addEventListener('load', async () => {
        try {
            const registration = await navigator.serviceWorker.register('/static/service-worker.js', {
                scope: '/'
            });

            console.log('[SW] Registered with scope:', registration.scope);

            // Проверяем обновления
            registration.addEventListener('updatefound', () => {
                const newWorker = registration.installing;

                newWorker.addEventListener('statechange', () => {
                    if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                        // Новая версия доступна
                        showUpdateNotification(registration);
                    }
                });
            });

            // Периодическая проверка обновлений (каждые 60 минут)
            setInterval(() => {
                registration.update();
            }, 60 * 60 * 1000);

        } catch (error) {
            console.error('[SW] Registration failed:', error);
        }
    });

    /**
     * Показывает уведомление о новой версии
     * @param {ServiceWorkerRegistration} registration
     */
    function showUpdateNotification(registration) {
        // Создаём уведомление
        const notification = document.createElement('div');
        notification.className = 'sw-update-notification';
        notification.innerHTML = `
            <div class="sw-update-content">
                <span>Доступна новая версия сайта</span>
                <button class="sw-update-btn" onclick="window.swUpdate()">Обновить</button>
                <button class="sw-update-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;

        // Стили
        const style = document.createElement('style');
        style.textContent = `
            .sw-update-notification {
                position: fixed;
                bottom: 20px;
                left: 50%;
                transform: translateX(-50%);
                background: var(--color-bg-secondary, #1a1a1a);
                border: 1px solid var(--color-accent, #D4A855);
                border-radius: 8px;
                padding: 12px 16px;
                z-index: 10000;
                box-shadow: 0 4px 20px rgba(0,0,0,0.5);
                animation: slideUp 0.3s ease;
            }
            .sw-update-content {
                display: flex;
                align-items: center;
                gap: 12px;
                color: var(--color-text, #fff);
                font-size: 14px;
            }
            .sw-update-btn {
                background: var(--color-accent, #D4A855);
                color: #000;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                cursor: pointer;
                font-weight: 500;
            }
            .sw-update-btn:hover {
                opacity: 0.9;
            }
            .sw-update-close {
                background: transparent;
                border: none;
                color: var(--color-text-muted, #888);
                font-size: 18px;
                cursor: pointer;
                padding: 0 4px;
            }
            @keyframes slideUp {
                from { transform: translateX(-50%) translateY(100px); opacity: 0; }
                to { transform: translateX(-50%) translateY(0); opacity: 1; }
            }
        `;

        document.head.appendChild(style);
        document.body.appendChild(notification);

        // Функция обновления
        window.swUpdate = function() {
            if (registration.waiting) {
                registration.waiting.postMessage({ type: 'SKIP_WAITING' });
            }
            window.location.reload();
        };
    }

    // Обработка события контроллера
    let refreshing = false;
    navigator.serviceWorker.addEventListener('controllerchange', () => {
        if (refreshing) return;
        refreshing = true;
        window.location.reload();
    });

    // Offline/Online индикация
    window.addEventListener('online', () => {
        document.body.classList.remove('offline');
        console.log('[SW] Back online');
    });

    window.addEventListener('offline', () => {
        document.body.classList.add('offline');
        console.log('[SW] Offline mode');
    });

    // Начальное состояние
    if (!navigator.onLine) {
        document.body.classList.add('offline');
    }
})();
