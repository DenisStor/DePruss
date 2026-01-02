/**
 * Sortable Table
 * Drag-and-drop table row reordering
 */
(function() {
    'use strict';

    class SortableTable {
        constructor(tableSelector, options = {}) {
            this.table = document.querySelector(tableSelector);
            if (!this.table) return;

            this.tbody = this.table.querySelector('tbody');
            this.options = {
                endpoint: options.endpoint || '/admin/api/reorder',
                ...options
            };

            this.draggedRow = null;
            this.init();
        }

        init() {
            this.table.classList.add('table--sortable');

            this.tbody.querySelectorAll('tr').forEach(row => {
                row.setAttribute('draggable', 'true');

                row.addEventListener('dragstart', (e) => this._onDragStart(e, row));
                row.addEventListener('dragend', () => this._onDragEnd(row));
                row.addEventListener('dragover', (e) => this._onDragOver(e, row));
                row.addEventListener('drop', (e) => this._onDrop(e, row));
            });
        }

        _onDragStart(e, row) {
            this.draggedRow = row;
            row.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
        }

        _onDragEnd(row) {
            row.classList.remove('dragging');
            this.tbody.querySelectorAll('tr').forEach(r => {
                r.classList.remove('drag-over', 'drag-over-bottom');
            });
            this.saveOrder();
        }

        _onDragOver(e, row) {
            e.preventDefault();
            if (row === this.draggedRow) return;

            const rect = row.getBoundingClientRect();
            const midY = rect.top + rect.height / 2;

            this.tbody.querySelectorAll('tr').forEach(r => {
                r.classList.remove('drag-over', 'drag-over-bottom');
            });

            if (e.clientY < midY) {
                row.classList.add('drag-over');
            } else {
                row.classList.add('drag-over-bottom');
            }
        }

        _onDrop(e, row) {
            e.preventDefault();
            if (row === this.draggedRow) return;

            const rect = row.getBoundingClientRect();
            const midY = rect.top + rect.height / 2;

            if (e.clientY < midY) {
                this.tbody.insertBefore(this.draggedRow, row);
            } else {
                this.tbody.insertBefore(this.draggedRow, row.nextSibling);
            }
        }

        async saveOrder() {
            const indicator = document.createElement('div');
            indicator.className = 'sort-saving';
            indicator.innerHTML = `
                <div class="sort-saving__spinner"></div>
                <span class="sort-saving__text">Сохранение порядка...</span>
            `;
            document.body.appendChild(indicator);

            const items = Array.from(this.tbody.querySelectorAll('tr')).map((row, index) => ({
                id: parseInt(row.dataset.id),
                sort_order: index
            }));

            try {
                const response = await fetch(this.options.endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ items })
                });

                if (response.ok) {
                    indicator.innerHTML = `
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--success)" stroke-width="2">
                            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                            <polyline points="22 4 12 14.01 9 11.01"></polyline>
                        </svg>
                        <span class="sort-saving__text">Сохранено!</span>
                    `;
                    setTimeout(() => indicator.remove(), 1500);
                } else {
                    throw new Error('Ошибка сохранения');
                }
            } catch (error) {
                indicator.remove();
                window.toast?.error('Ошибка', 'Не удалось сохранить порядок');
            }
        }
    }

    window.SortableTable = SortableTable;
})();
