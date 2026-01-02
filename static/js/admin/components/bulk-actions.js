/**
 * Bulk Actions
 * Multi-select table operations
 */
(function() {
    'use strict';

    class BulkActions {
        constructor(options) {
            this.tableSelector = options.tableSelector || '.table';
            this.checkboxSelector = options.checkboxSelector || '.bulk-checkbox';
            this.selectAllSelector = options.selectAllSelector || '#selectAll';
            this.toolbarSelector = options.toolbarSelector || '.bulk-toolbar';
            this.countSelector = options.countSelector || '.bulk-count';
            this.apiEndpoint = options.apiEndpoint;

            this.init();
        }

        init() {
            this.table = document.querySelector(this.tableSelector);
            this.toolbar = document.querySelector(this.toolbarSelector);
            this.countEl = document.querySelector(this.countSelector);
            this.selectAll = document.querySelector(this.selectAllSelector);

            if (!this.table) return;
            this.bindEvents();
        }

        bindEvents() {
            if (this.selectAll) {
                this.selectAll.addEventListener('change', (e) => {
                    const checkboxes = this.table.querySelectorAll(this.checkboxSelector);
                    checkboxes.forEach(cb => cb.checked = e.target.checked);
                    this.updateToolbar();
                });
            }

            this.table.addEventListener('change', (e) => {
                if (e.target.matches(this.checkboxSelector)) {
                    this.updateToolbar();
                    this.updateSelectAll();
                }
            });

            this.toolbar?.querySelectorAll('[data-action]').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const action = e.currentTarget.dataset.action;
                    this.performAction(action);
                });
            });
        }

        getSelectedIds() {
            const checkboxes = this.table.querySelectorAll(this.checkboxSelector + ':checked');
            return Array.from(checkboxes).map(cb => parseInt(cb.value));
        }

        updateToolbar() {
            const count = this.getSelectedIds().length;
            if (this.toolbar) {
                this.toolbar.classList.toggle('active', count > 0);
            }
            if (this.countEl) {
                this.countEl.textContent = count;
            }
        }

        updateSelectAll() {
            if (!this.selectAll) return;
            const checkboxes = this.table.querySelectorAll(this.checkboxSelector);
            const checked = this.table.querySelectorAll(this.checkboxSelector + ':checked');
            this.selectAll.checked = checkboxes.length === checked.length;
            this.selectAll.indeterminate = checked.length > 0 && checked.length < checkboxes.length;
        }

        async performAction(action) {
            const ids = this.getSelectedIds();
            if (ids.length === 0) return;

            if (action === 'delete') {
                const confirmed = await window.modal.confirm({
                    title: 'Удалить выбранные?',
                    message: `Вы уверены, что хотите удалить <strong>${ids.length}</strong> элемент(ов)? Это действие нельзя отменить.`,
                    confirmText: 'Удалить',
                    cancelText: 'Отмена'
                });
                if (!confirmed) return;
            }

            try {
                const response = await fetch(this.apiEndpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ids, action })
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Ошибка выполнения');
                }

                window.toast?.success('Успешно', 'Операция выполнена');
                setTimeout(() => window.location.reload(), 500);
            } catch (err) {
                window.toast?.error('Ошибка', err.message);
            }
        }
    }

    window.BulkActions = BulkActions;
})();
