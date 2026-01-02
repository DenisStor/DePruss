/**
 * Form Validator
 * Client-side form validation with custom rules
 */
(function() {
    'use strict';

    class FormValidator {
        constructor(form, rules = {}) {
            this.form = typeof form === 'string' ? document.querySelector(form) : form;
            this.rules = rules;
            this.errors = {};

            if (this.form) {
                this.init();
            }
        }

        init() {
            this.form.setAttribute('novalidate', '');

            this.form.addEventListener('submit', (e) => {
                if (!this.validate()) {
                    e.preventDefault();
                    this.showErrors();
                }
            });

            // Real-time validation
            this.form.querySelectorAll('input, select, textarea').forEach(field => {
                field.addEventListener('blur', () => this.validateField(field.name));
                field.addEventListener('input', () => {
                    if (this.errors[field.name]) {
                        this.validateField(field.name);
                    }
                });
            });
        }

        validate() {
            this.errors = {};
            let isValid = true;

            for (const fieldName of Object.keys(this.rules)) {
                if (!this.validateField(fieldName)) {
                    isValid = false;
                }
            }

            return isValid;
        }

        validateField(fieldName) {
            const field = this.form.querySelector(`[name="${fieldName}"]`);
            const rules = this.rules[fieldName];

            if (!field || !rules) return true;

            const value = field.value.trim();
            delete this.errors[fieldName];

            for (const rule of rules) {
                if (rule.required && !value) {
                    this.errors[fieldName] = rule.message || 'Обязательное поле';
                    break;
                }
                if (rule.minLength && value.length < rule.minLength) {
                    this.errors[fieldName] = rule.message || `Минимум ${rule.minLength} символов`;
                    break;
                }
                if (rule.maxLength && value.length > rule.maxLength) {
                    this.errors[fieldName] = rule.message || `Максимум ${rule.maxLength} символов`;
                    break;
                }
                if (rule.pattern && !rule.pattern.test(value)) {
                    this.errors[fieldName] = rule.message || 'Неверный формат';
                    break;
                }
                if (rule.custom && !rule.custom(value, this.form)) {
                    this.errors[fieldName] = rule.message || 'Ошибка валидации';
                    break;
                }
            }

            this.updateFieldUI(field, this.errors[fieldName]);
            return !this.errors[fieldName];
        }

        updateFieldUI(field, error) {
            const wrapper = field.closest('.form-group');
            if (!wrapper) return;

            const existingError = wrapper.querySelector('.form-error');
            existingError?.remove();

            if (error) {
                field.classList.add('form-input--error');
                const errorEl = document.createElement('span');
                errorEl.className = 'form-error';
                errorEl.textContent = error;
                wrapper.appendChild(errorEl);
            } else {
                field.classList.remove('form-input--error');
            }
        }

        showErrors() {
            const firstError = this.form.querySelector('.form-input--error');
            firstError?.focus();
            window.toast?.error('Ошибка', 'Проверьте заполнение формы');
        }
    }

    window.FormValidator = FormValidator;
})();
