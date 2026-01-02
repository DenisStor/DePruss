/**
 * Network Adapter - определение качества соединения и адаптивная загрузка
 * Использует Network Information API с fallback для старых браузеров
 */

(function() {
    'use strict';

    /**
     * Определяет качество сети и предлагает оптимальные настройки загрузки
     */
    class NetworkAdapter {
        constructor() {
            this.connection = navigator.connection ||
                             navigator.mozConnection ||
                             navigator.webkitConnection;

            this.quality = this.detectQuality();
            this.saveData = this.connection?.saveData || false;
            this.isOnline = navigator.onLine;

            // Кеш для AVIF поддержки
            this._avifSupported = null;

            // Слушаем изменения сети
            this._setupListeners();
        }

        /**
         * Определяет качество сети
         * @returns {'offline'|'slow-2g'|'2g'|'3g'|'4g'|'unknown'}
         */
        detectQuality() {
            if (!navigator.onLine) {
                return 'offline';
            }

            if (!this.connection) {
                return 'unknown';
            }

            const type = this.connection.effectiveType;
            const downlink = this.connection.downlink; // Mbps
            const rtt = this.connection.rtt; // ms

            // Используем effectiveType как основу
            if (type === 'slow-2g' || type === '2g') {
                return type;
            }

            // Дополнительная проверка по метрикам
            if (type === '3g') {
                // Плохой 3G
                if (rtt > 800 || downlink < 0.5) {
                    return '2g';
                }
                return '3g';
            }

            if (type === '4g') {
                // Проверяем реальные показатели
                if (rtt > 400 || downlink < 1.5) {
                    return '3g';
                }
                return '4g';
            }

            return 'unknown';
        }

        /**
         * Возвращает рекомендуемый размер изображения для текущей сети
         * @returns {'tiny'|'thumbnail'|'small'|'medium'|'large'}
         */
        getImageSize() {
            // Если включен режим экономии данных
            if (this.saveData) {
                return 'thumbnail';
            }

            switch (this.quality) {
                case 'offline':
                    return 'thumbnail'; // Из кеша
                case 'slow-2g':
                    return 'tiny';
                case '2g':
                    return 'thumbnail';
                case '3g':
                    return 'small';
                case '4g':
                    return 'medium';
                default:
                    return 'small'; // Безопасный default
            }
        }

        /**
         * Проверяет нужно ли предзагружать изображения
         * @returns {boolean}
         */
        shouldPreload() {
            return this.quality === '4g' && !this.saveData && this.isOnline;
        }

        /**
         * Проверяет нужно ли автоматически загружать изображения
         * @returns {boolean}
         */
        shouldAutoLoad() {
            // На очень медленных соединениях загружаем только по запросу
            return this.quality !== 'slow-2g' && this.quality !== 'offline';
        }

        /**
         * Проверяет поддержку AVIF (кешируется)
         * @returns {Promise<boolean>}
         */
        async supportsAvif() {
            if (this._avifSupported !== null) {
                return this._avifSupported;
            }

            return new Promise((resolve) => {
                const img = new Image();
                img.onload = () => {
                    this._avifSupported = img.width === 1;
                    resolve(this._avifSupported);
                };
                img.onerror = () => {
                    this._avifSupported = false;
                    resolve(false);
                };
                // Минимальный AVIF (1x1 пиксель)
                img.src = 'data:image/avif;base64,AAAAIGZ0eXBhdmlmAAAAAGF2aWZtaWYxbWlhZk1BMUIAAADybWV0YQAAAAAAAAAoaGRscgAAAAAAAAAAcGljdAAAAAAAAAAAAAAAAGxpYmF2aWYAAAAADnBpdG0AAAAAAAEAAAAeaWxvYwAAAABEAAABAAEAAAABAAABGgAAAB0AAAAoaWluZgAAAAAAAQAAABppbmZlAgAAAAABAABhdjAxQ29sb3IAAAAAamlwcnAAAABLaXBjbwAAABRpc3BlAAAAAAAAAAIAAAACAAAAEHBpeGkAAAAAAwgICAAAAAxhdjFDgQ0MAAAAABNjb2xybmNseAACAAIAAYAAAAAXaXBtYQAAAAAAAAABAAEEAQKDBAAAACVtZGF0EgAKBzgABc0WAAIAEQEiAAAAAQAAAAbTq';
            });
        }

        /**
         * Получает информацию о текущем состоянии сети
         * @returns {Object}
         */
        getNetworkInfo() {
            return {
                quality: this.quality,
                saveData: this.saveData,
                isOnline: this.isOnline,
                effectiveType: this.connection?.effectiveType || 'unknown',
                downlink: this.connection?.downlink || null,
                rtt: this.connection?.rtt || null,
                recommendedImageSize: this.getImageSize(),
                shouldPreload: this.shouldPreload(),
                shouldAutoLoad: this.shouldAutoLoad()
            };
        }

        /**
         * Настраивает слушатели событий сети
         * @private
         */
        _setupListeners() {
            // Изменение состояния онлайн/офлайн
            window.addEventListener('online', () => {
                this.isOnline = true;
                this.quality = this.detectQuality();
                this._dispatchChange();
            });

            window.addEventListener('offline', () => {
                this.isOnline = false;
                this.quality = 'offline';
                this._dispatchChange();
            });

            // Изменение типа соединения
            if (this.connection) {
                this.connection.addEventListener('change', () => {
                    this.quality = this.detectQuality();
                    this.saveData = this.connection.saveData;
                    this._dispatchChange();
                });
            }
        }

        /**
         * Отправляет событие изменения сети
         * @private
         */
        _dispatchChange() {
            window.dispatchEvent(new CustomEvent('networkchange', {
                detail: this.getNetworkInfo()
            }));
        }
    }

    // Создаем глобальный экземпляр
    window.networkAdapter = new NetworkAdapter();

    // Экспортируем класс для возможного расширения
    window.NetworkAdapter = NetworkAdapter;
})();
