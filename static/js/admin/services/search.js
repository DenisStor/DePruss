/**
 * Global Search
 * Full-text search across dishes and categories
 */
(function() {
    'use strict';

    class GlobalSearch {
        constructor(options = {}) {
            this.apiEndpoint = options.apiEndpoint || '/admin/api/search';
            this.minChars = options.minChars || 2;
            this.debounceTime = options.debounceTime || 300;
            this.container = null;
            this.input = null;
            this.results = null;
            this.debounceTimer = null;
        }

        init() {
            this.createUI();
            this.bindEvents();
        }

        createUI() {
            this.container = document.createElement('div');
            this.container.className = 'global-search';
            this.container.innerHTML = `
                <div class="global-search__backdrop"></div>
                <div class="global-search__dialog">
                    <div class="global-search__input-wrapper">
                        <svg class="global-search__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="11" cy="11" r="8"></circle>
                            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                        </svg>
                        <input type="text" class="global-search__input" placeholder="Поиск блюд, категорий...">
                        <kbd class="global-search__kbd">ESC</kbd>
                    </div>
                    <div class="global-search__results"></div>
                </div>
            `;
            document.body.appendChild(this.container);

            this.input = this.container.querySelector('.global-search__input');
            this.results = this.container.querySelector('.global-search__results');
        }

        bindEvents() {
            document.addEventListener('keydown', (e) => {
                if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
                    e.preventDefault();
                    this.open();
                }
                if (e.key === 'Escape' && this.container.classList.contains('active')) {
                    this.close();
                }
            });

            this.container.querySelector('.global-search__backdrop').addEventListener('click', () => this.close());

            this.input.addEventListener('input', () => {
                clearTimeout(this.debounceTimer);
                this.debounceTimer = setTimeout(() => this.search(), this.debounceTime);
            });
        }

        open() {
            this.container.classList.add('active');
            this.input.value = '';
            this.results.innerHTML = '';
            this.input.focus();
        }

        close() {
            this.container.classList.remove('active');
        }

        async search() {
            const query = this.input.value.trim();
            if (query.length < this.minChars) {
                this.results.innerHTML = '<p class="global-search__hint">Введите минимум 2 символа</p>';
                return;
            }

            this.results.innerHTML = '<p class="global-search__loading">Поиск...</p>';

            try {
                const response = await fetch(`${this.apiEndpoint}?q=${encodeURIComponent(query)}`);
                const data = await response.json();
                this.renderResults(data);
            } catch (err) {
                this.results.innerHTML = '<p class="global-search__error">Ошибка поиска</p>';
            }
        }

        renderResults(data) {
            if (!data.dishes?.length && !data.categories?.length) {
                this.results.innerHTML = '<p class="global-search__empty">Ничего не найдено</p>';
                return;
            }

            let html = '';

            if (data.dishes?.length) {
                html += '<div class="global-search__group"><h4>Блюда</h4>';
                data.dishes.forEach(dish => {
                    html += `
                        <a href="/admin/dishes/${dish.id}/edit" class="global-search__item">
                            <span class="global-search__item-name">${dish.name}</span>
                            <span class="global-search__item-meta">${dish.category}</span>
                        </a>
                    `;
                });
                html += '</div>';
            }

            if (data.categories?.length) {
                html += '<div class="global-search__group"><h4>Категории</h4>';
                data.categories.forEach(cat => {
                    html += `
                        <a href="/admin/categories/${cat.id}/edit" class="global-search__item">
                            <span class="global-search__item-name">${cat.name}</span>
                        </a>
                    `;
                });
                html += '</div>';
            }

            this.results.innerHTML = html;
        }
    }

    window.GlobalSearch = GlobalSearch;
})();
