/**
 * Progressive Image Loader
 * Загружает изображения прогрессивно в зависимости от скорости сети
 *
 * Последовательность:
 * 1. Мгновенно: CSS background-color (dominant color)
 * 2. <50ms: tiny placeholder (inline base64)
 * 3. По viewport: целевой размер по Network API
 * 4. Поддержка AVIF с fallback на WebP
 */

(function() {
    'use strict';

    // Ждём загрузки NetworkAdapter
    if (!window.networkAdapter) {
        console.warn('NetworkAdapter not loaded, using default behavior');
    }

    /**
     * Управляет прогрессивной загрузкой одного изображения
     */
    class ProgressiveImage {
        /**
         * @param {HTMLImageElement} img - Элемент изображения
         */
        constructor(img) {
            this.img = img;
            this.container = img.closest('.progressive-image') || img.parentElement;
            this.loaded = false;
            this.loading = false;
        }

        /**
         * Определяет лучший URL для текущей сети
         * @returns {Promise<string>}
         */
        async getBestUrl() {
            const adapter = window.networkAdapter;
            const targetSize = adapter ? adapter.getImageSize() : 'small';
            const supportsAvif = adapter ? await adapter.supportsAvif() : false;

            // Пробуем AVIF если поддерживается
            if (supportsAvif) {
                const avifUrl = this.img.dataset[`avif${this._capitalize(targetSize)}`] ||
                               this.img.dataset[`${targetSize}Avif`];
                if (avifUrl) {
                    return avifUrl;
                }
            }

            // Fallback на WebP
            const webpUrl = this.img.dataset[targetSize] ||
                           this.img.dataset.src;

            return webpUrl || this.img.src;
        }

        /**
         * Загружает изображение
         * @returns {Promise<void>}
         */
        async load() {
            if (this.loaded || this.loading) {
                return;
            }

            this.loading = true;
            this.container?.classList.add('loading');

            try {
                const url = await this.getBestUrl();

                if (!url || url === this.img.src) {
                    this._onLoaded();
                    return;
                }

                // Предзагружаем изображение
                await this._preload(url);

                // Заменяем src
                this.img.src = url;

                // Устанавливаем srcset если доступен
                this._applySrcset();

                this._onLoaded();

            } catch (error) {
                console.warn('Progressive image load failed:', error);
                this.img.classList.add('error');
            } finally {
                this.loading = false;
                this.container?.classList.remove('loading');
            }
        }

        /**
         * Предзагрузка изображения
         * @param {string} url
         * @returns {Promise<void>}
         * @private
         */
        _preload(url) {
            return new Promise((resolve, reject) => {
                const img = new Image();
                img.onload = resolve;
                img.onerror = reject;
                img.src = url;
            });
        }

        /**
         * Применяет srcset с учётом AVIF
         * @private
         */
        async _applySrcset() {
            const adapter = window.networkAdapter;
            const supportsAvif = adapter ? await adapter.supportsAvif() : false;

            // Пробуем AVIF srcset
            if (supportsAvif && this.img.dataset.avifSrcset) {
                this.img.srcset = this.img.dataset.avifSrcset;
            } else if (this.img.dataset.srcset) {
                this.img.srcset = this.img.dataset.srcset;
            }
        }

        /**
         * Обработчик успешной загрузки
         * @private
         */
        _onLoaded() {
            this.loaded = true;
            this.img.classList.remove('blur-up');
            this.img.classList.add('loaded');

            // Очищаем data-атрибуты
            delete this.img.dataset.src;
            delete this.img.dataset.srcset;
        }

        /**
         * Capitalize первой буквы
         * @param {string} str
         * @returns {string}
         * @private
         */
        _capitalize(str) {
            return str.charAt(0).toUpperCase() + str.slice(1);
        }
    }

    /**
     * Менеджер прогрессивных изображений
     */
    class ProgressiveImageManager {
        constructor() {
            this.images = new Map();
            this.observer = null;

            this._init();
        }

        /**
         * Инициализация
         * @private
         */
        _init() {
            // Проверяем поддержку Intersection Observer
            if (!('IntersectionObserver' in window)) {
                this._loadAllImmediately();
                return;
            }

            this._setupObserver();
            this._observeImages();
            this._setupNetworkListener();
        }

        /**
         * Настройка Intersection Observer
         * @private
         */
        _setupObserver() {
            const adapter = window.networkAdapter;
            // На быстрой сети загружаем заранее, на медленной - точно в viewport
            const rootMargin = adapter?.shouldPreload() ? '400px' : '100px';

            this.observer = new IntersectionObserver(
                (entries) => this._onIntersect(entries),
                {
                    root: null,
                    rootMargin: rootMargin,
                    threshold: 0.01
                }
            );
        }

        /**
         * Обработчик пересечения viewport
         * @param {IntersectionObserverEntry[]} entries
         * @private
         */
        _onIntersect(entries) {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) {
                    return;
                }

                const img = entry.target;
                const progressive = this.images.get(img);

                if (progressive && !progressive.loaded) {
                    // Проверяем нужно ли автозагружать
                    const adapter = window.networkAdapter;
                    if (!adapter || adapter.shouldAutoLoad()) {
                        progressive.load();
                    }
                }

                this.observer.unobserve(img);
            });
        }

        /**
         * Начинает наблюдение за изображениями
         * @private
         */
        _observeImages() {
            const selector = 'img[data-src], img.blur-up[data-small], img.blur-up[data-medium]';
            document.querySelectorAll(selector).forEach((img) => {
                if (!this.images.has(img)) {
                    this.images.set(img, new ProgressiveImage(img));
                    this.observer.observe(img);
                }
            });
        }

        /**
         * Fallback для старых браузеров
         * @private
         */
        _loadAllImmediately() {
            const selector = 'img[data-src], img.blur-up';
            document.querySelectorAll(selector).forEach((img) => {
                const progressive = new ProgressiveImage(img);
                progressive.load();
            });
        }

        /**
         * Слушатель изменения сети
         * @private
         */
        _setupNetworkListener() {
            window.addEventListener('networkchange', (e) => {
                const info = e.detail;

                // Если соединение улучшилось, можем загрузить более качественные изображения
                if (info.quality === '4g' && !info.saveData) {
                    this._upgradeLoadedImages();
                }
            });
        }

        /**
         * Обновляет уже загруженные изображения до лучшего качества
         * @private
         */
        async _upgradeLoadedImages() {
            // Только для изображений в viewport
            const visible = document.querySelectorAll('img.loaded[data-medium], img.loaded[data-large]');

            for (const img of visible) {
                const rect = img.getBoundingClientRect();
                const inViewport = rect.top < window.innerHeight && rect.bottom > 0;

                if (inViewport) {
                    const progressive = this.images.get(img) || new ProgressiveImage(img);
                    progressive.loaded = false; // Сбрасываем для апгрейда
                    await progressive.load();
                }
            }
        }

        /**
         * Повторно сканирует DOM для новых изображений
         * Вызывайте после динамического добавления контента
         */
        refresh() {
            this._observeImages();
        }

        /**
         * Принудительно загружает изображение
         * @param {HTMLImageElement} img
         */
        forceLoad(img) {
            let progressive = this.images.get(img);
            if (!progressive) {
                progressive = new ProgressiveImage(img);
                this.images.set(img, progressive);
            }
            progressive.load();
        }
    }

    // Создаём глобальный менеджер при загрузке DOM
    let manager = null;

    function init() {
        if (manager) return;
        manager = new ProgressiveImageManager();
        window.progressiveImages = manager;
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Экспорт для динамически добавленных изображений
    window.refreshProgressiveImages = function() {
        if (manager) {
            manager.refresh();
        }
    };
})();
