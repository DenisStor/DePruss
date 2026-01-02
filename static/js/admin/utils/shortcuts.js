/**
 * Keyboard Shortcuts - Global keyboard shortcut handler with help modal
 */
(function() {
    'use strict';

    class KeyboardShortcuts {
        constructor() {
            this.shortcuts = new Map();
            this.descriptions = new Map();
            this.init();
        }

        init() {
            document.addEventListener('keydown', (e) => {
                if (e.target.matches('input, textarea, select') && e.key !== 'Escape') return;
                const handler = this.shortcuts.get(this.getKeyCombo(e));
                if (handler) { e.preventDefault(); handler(e); }
            });
            this.registerDefaults();
        }

        getKeyCombo(e) {
            const parts = [];
            if (e.metaKey || e.ctrlKey) parts.push('cmd');
            if (e.shiftKey) parts.push('shift');
            if (e.altKey) parts.push('alt');
            parts.push(e.key.toLowerCase());
            return parts.join('+');
        }

        register(combo, handler, description = '') {
            this.shortcuts.set(combo.toLowerCase(), handler);
            if (description) this.descriptions.set(combo.toLowerCase(), description);
        }

        unregister(combo) {
            this.shortcuts.delete(combo.toLowerCase());
            this.descriptions.delete(combo.toLowerCase());
        }

        registerDefaults() {
            this.register('cmd+k', () => {
                const m = document.getElementById('globalSearchModal');
                if (m) { m.classList.add('active'); m.querySelector('.search-modal__input')?.focus(); }
            }, 'Глобальный поиск');

            this.register('cmd+n', () => {
                const p = window.location.pathname;
                if (p.includes('/dishes')) window.location.href = '/admin/dishes/new';
                else if (p.includes('/categories')) window.location.href = '/admin/categories/new';
                else if (p.includes('/users')) window.location.href = '/admin/users/new';
            }, 'Создать новую запись');

            this.register('shift+/', () => this.showHelp(), 'Показать справку');
            this.register('g', () => this.waitForSecondKey('d', () => window.location.href = '/admin'), 'Перейти на главную');

            this.register('escape', () => {
                const m = document.getElementById('globalSearchModal');
                if (m?.classList.contains('active')) { m.classList.remove('active'); return; }
                window.tableNavigator?.clearSelection();
            }, 'Закрыть/Отменить');
        }

        waitForSecondKey(key, callback, timeout = 500) {
            const handler = (e) => {
                if (e.key.toLowerCase() === key) { e.preventDefault(); callback(); }
                document.removeEventListener('keydown', handler);
                clearTimeout(timer);
            };
            document.addEventListener('keydown', handler);
            const timer = setTimeout(() => document.removeEventListener('keydown', handler), timeout);
        }

        showHelp() {
            const content = `
                <div class="modal__header">
                    <h3 class="modal__title"><svg class="modal__title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>Горячие клавиши</h3>
                    <button class="modal__close" data-action="close"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg></button>
                </div>
                <div class="modal__body">
                    <div class="shortcuts-list">
                        <div class="shortcuts-group"><h4>Навигация</h4>
                            <div class="shortcut-item"><kbd>Cmd</kbd><kbd>K</kbd><span>Глобальный поиск</span></div>
                            <div class="shortcut-item"><kbd>Cmd</kbd><kbd>N</kbd><span>Создать новую запись</span></div>
                            <div class="shortcut-item"><kbd>G</kbd> затем <kbd>D</kbd><span>Перейти на главную</span></div>
                        </div>
                        <div class="shortcuts-group"><h4>Таблицы</h4>
                            <div class="shortcut-item"><kbd>J</kbd>/<kbd>K</kbd><span>Навигация вверх/вниз</span></div>
                            <div class="shortcut-item"><kbd>Enter</kbd><span>Редактировать выбранное</span></div>
                            <div class="shortcut-item"><kbd>Delete</kbd><span>Удалить выбранное</span></div>
                            <div class="shortcut-item"><kbd>Space</kbd><span>Выбрать/снять выделение</span></div>
                        </div>
                        <div class="shortcuts-group"><h4>Общие</h4>
                            <div class="shortcut-item"><kbd>Esc</kbd><span>Закрыть/Отменить</span></div>
                            <div class="shortcut-item"><kbd>?</kbd><span>Показать эту справку</span></div>
                        </div>
                    </div>
                </div>
                <div class="modal__footer"><button class="btn btn--secondary" data-action="close">Закрыть</button></div>`;
            const modalEl = window.modal.open(content);
            modalEl.addEventListener('click', (e) => { if (e.target.closest('[data-action="close"]')) window.modal.close(); });
        }
    }

    window.KeyboardShortcuts = KeyboardShortcuts;
})();
