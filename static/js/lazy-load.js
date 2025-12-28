/**
 * Lazy loading с Intersection Observer для оптимизации 3G
 * LQIP (Low Quality Image Placeholder) pattern
 */

(function() {
    'use strict';

    // Проверяем поддержку IntersectionObserver
    if (!('IntersectionObserver' in window)) {
        // Fallback для старых браузеров - загружаем все сразу
        document.querySelectorAll('img[data-src]').forEach(function(img) {
            img.src = img.dataset.src;
            img.classList.add('loaded');
        });
        return;
    }

    // Опции наблюдателя
    var options = {
        root: null,
        rootMargin: '200px', // Загружаем за 200px до появления
        threshold: 0.01
    };

    // Функция загрузки изображения
    function loadImage(img) {
        var src = img.dataset.src;
        var srcset = img.dataset.srcset;
        if (!src) return;

        // Создаем новый Image для предзагрузки
        var newImg = new Image();

        newImg.onload = function() {
            img.src = src;
            if (srcset) {
                img.srcset = srcset;
                img.removeAttribute('data-srcset');
            }
            img.classList.remove('blur-up');
            img.classList.add('loaded');
            img.removeAttribute('data-src');
        };

        newImg.onerror = function() {
            // При ошибке оставляем placeholder
            img.classList.add('error');
        };

        newImg.src = src;
    }

    // Создаем наблюдатель
    var observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                var img = entry.target;
                loadImage(img);
                observer.unobserve(img);
            }
        });
    }, options);

    // Наблюдаем за всеми изображениями с data-src
    function observeImages() {
        document.querySelectorAll('img[data-src]').forEach(function(img) {
            observer.observe(img);
        });
    }

    // Запускаем при загрузке DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', observeImages);
    } else {
        observeImages();
    }

    // Экспортируем для динамически добавленных изображений
    window.lazyLoadImages = observeImages;
})();
