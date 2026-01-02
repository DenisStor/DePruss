/**
 * Table Navigator
 * Keyboard navigation for table rows
 */
(function() {
    'use strict';

    class TableNavigator {
        constructor(options = {}) {
            this.tableSelector = options.tableSelector || '.admin-table';
            this.rowSelector = options.rowSelector || 'tbody tr[data-id]';
            this.selectedClass = options.selectedClass || 'table-row--selected';
            this.editUrlPattern = options.editUrlPattern || null;
            this.deleteCallback = options.deleteCallback || null;

            this.table = document.querySelector(this.tableSelector);
            this.selectedIndex = -1;

            if (this.table) {
                this.init();
            }
        }

        init() {
            this.bindKeyboard();
            this.bindClick();
        }

        getRows() {
            return Array.from(this.table.querySelectorAll(this.rowSelector));
        }

        bindKeyboard() {
            document.addEventListener('keydown', (e) => {
                if (e.target.matches('input, textarea, select')) return;

                const rows = this.getRows();
                if (rows.length === 0) return;

                switch (e.key.toLowerCase()) {
                    case 'j':
                        e.preventDefault();
                        this.selectRow(Math.min(this.selectedIndex + 1, rows.length - 1));
                        break;
                    case 'k':
                        e.preventDefault();
                        this.selectRow(Math.max(this.selectedIndex - 1, 0));
                        break;
                    case 'enter':
                        if (this.selectedIndex >= 0) {
                            e.preventDefault();
                            this.editSelected();
                        }
                        break;
                    case 'delete':
                    case 'backspace':
                        if (this.selectedIndex >= 0 && !e.metaKey && !e.ctrlKey) {
                            e.preventDefault();
                            this.deleteSelected();
                        }
                        break;
                    case ' ':
                        if (this.selectedIndex >= 0) {
                            e.preventDefault();
                            this.toggleCheckbox();
                        }
                        break;
                }
            });
        }

        bindClick() {
            this.table.addEventListener('click', (e) => {
                const row = e.target.closest(this.rowSelector);
                if (row && !e.target.closest('a, button, input, .toggle-switch')) {
                    const rows = this.getRows();
                    const index = rows.indexOf(row);
                    this.selectRow(index);
                }
            });
        }

        selectRow(index) {
            const rows = this.getRows();
            if (index < 0 || index >= rows.length) return;

            rows.forEach(row => row.classList.remove(this.selectedClass));

            this.selectedIndex = index;
            const row = rows[index];
            row.classList.add(this.selectedClass);
            row.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        }

        clearSelection() {
            const rows = this.getRows();
            rows.forEach(row => row.classList.remove(this.selectedClass));
            this.selectedIndex = -1;
        }

        getSelectedRow() {
            const rows = this.getRows();
            return this.selectedIndex >= 0 ? rows[this.selectedIndex] : null;
        }

        editSelected() {
            const row = this.getSelectedRow();
            if (!row) return;

            const editLink = row.querySelector('a[href*="/edit"]');
            if (editLink) {
                window.location.href = editLink.href;
                return;
            }

            if (this.editUrlPattern) {
                window.location.href = this.editUrlPattern.replace('{id}', row.dataset.id);
            }
        }

        deleteSelected() {
            const row = this.getSelectedRow();
            if (!row) return;

            const deleteBtn = row.querySelector('[data-action="delete"], .btn--danger');
            if (deleteBtn) {
                deleteBtn.click();
                return;
            }

            if (this.deleteCallback) {
                this.deleteCallback(row.dataset.id, row);
            }
        }

        toggleCheckbox() {
            const row = this.getSelectedRow();
            if (!row) return;

            const checkbox = row.querySelector('input[type="checkbox"].bulk-checkbox');
            if (checkbox) {
                checkbox.checked = !checkbox.checked;
                checkbox.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }
    }

    window.TableNavigator = TableNavigator;
})();
