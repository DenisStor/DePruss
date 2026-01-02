/**
 * Inline Editor
 * Double-click to edit table cell values
 */
(function() {
    'use strict';

    class InlineEditor {
        constructor(options = {}) {
            this.selector = options.selector || '[data-editable]';
            this.apiEndpoint = options.apiEndpoint;
            this.init();
        }

        init() {
            document.querySelectorAll(this.selector).forEach(el => {
                el.addEventListener('dblclick', () => this.startEdit(el));
            });
        }

        startEdit(element) {
            if (element.querySelector('input, select')) return;

            const field = element.dataset.field;
            const type = element.dataset.type || 'text';
            const value = element.dataset.value || element.textContent.trim();
            const entityId = element.closest('[data-id]')?.dataset.id;

            const originalContent = element.innerHTML;
            const input = this._createInput(type, value);

            element.innerHTML = '';
            element.appendChild(input);
            input.focus();
            input.select();

            const save = () => this._saveValue(input, element, field, type, entityId, value, originalContent);

            input.addEventListener('blur', save);
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    input.blur();
                }
                if (e.key === 'Escape') {
                    element.innerHTML = originalContent;
                }
            });
        }

        _createInput(type, value) {
            let input;

            if (type === 'boolean') {
                input = document.createElement('select');
                input.innerHTML = `
                    <option value="true" ${value === 'true' ? 'selected' : ''}>Да</option>
                    <option value="false" ${value === 'false' ? 'selected' : ''}>Нет</option>
                `;
            } else if (type === 'number') {
                input = document.createElement('input');
                input.type = 'number';
                input.value = value;
            } else {
                input = document.createElement('input');
                input.type = 'text';
                input.value = value;
            }

            input.className = 'inline-edit-input';
            return input;
        }

        async _saveValue(input, element, field, type, entityId, oldValue, originalContent) {
            const newValue = input.value;

            if (newValue === oldValue) {
                element.innerHTML = originalContent;
                return;
            }

            try {
                const response = await fetch(`${this.apiEndpoint}/${entityId}`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        [field]: type === 'number' ? parseFloat(newValue) : newValue
                    })
                });

                if (!response.ok) throw new Error('Ошибка сохранения');

                element.textContent = newValue;
                element.dataset.value = newValue;
                window.toast?.success('Сохранено', 'Изменения применены');
            } catch (err) {
                element.innerHTML = originalContent;
                window.toast?.error('Ошибка', 'Не удалось сохранить');
            }
        }
    }

    window.InlineEditor = InlineEditor;
})();
