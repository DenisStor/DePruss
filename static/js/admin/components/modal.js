/**
 * Modal Dialog Manager
 * Handles confirm dialogs, previews, and form modals
 */
(function() {
    'use strict';

    const CLOSE_ICON = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';

    class ModalManager {
        constructor() {
            this.overlay = document.createElement('div');
            this.overlay.className = 'modal-overlay';
            document.body.appendChild(this.overlay);

            this.overlay.addEventListener('click', (e) => {
                if (e.target === this.overlay) this.close();
            });

            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && this.overlay.classList.contains('active')) this.close();
            });
        }

        open(content, options = {}) {
            const modalEl = document.createElement('div');
            modalEl.className = `modal ${options.large ? 'modal--large' : ''}`;
            modalEl.innerHTML = content;
            this.overlay.innerHTML = '';
            this.overlay.appendChild(modalEl);
            this.overlay.classList.add('active');
            document.body.style.overflow = 'hidden';
            modalEl.querySelector('button, a.btn')?.focus();
            return modalEl;
        }

        close() {
            this.overlay.classList.remove('active');
            document.body.style.overflow = '';
        }

        confirm(options) {
            return new Promise((resolve) => {
                const content = `
                    <div class="modal__header">
                        <h3 class="modal__title">
                            <svg class="modal__title-icon modal__title-icon--danger" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
                            ${options.title || 'Подтверждение'}
                        </h3>
                        <button class="modal__close" data-action="close">${CLOSE_ICON}</button>
                    </div>
                    <div class="modal__body"><p class="modal__text">${options.message}</p></div>
                    <div class="modal__footer">
                        <button class="btn btn--secondary" data-action="cancel">${options.cancelText || 'Отмена'}</button>
                        <button class="btn btn--danger" data-action="confirm">${options.confirmText || 'Удалить'}</button>
                    </div>`;
                const modalEl = this.open(content);
                modalEl.addEventListener('click', (e) => {
                    const action = e.target.closest('[data-action]')?.dataset.action;
                    if (action === 'confirm') { this.close(); resolve(true); }
                    else if (action === 'cancel' || action === 'close') { this.close(); resolve(false); }
                });
            });
        }

        preview(dish) {
            const info = [
                `<div class="dish-preview__row"><span class="dish-preview__label">Категория</span><span class="dish-preview__value">${dish.category}</span></div>`,
                `<div class="dish-preview__row"><span class="dish-preview__label">Цена</span><span class="dish-preview__value">${dish.price} </span></div>`,
                dish.weight ? `<div class="dish-preview__row"><span class="dish-preview__label">Вес</span><span class="dish-preview__value">${dish.weight}</span></div>` : '',
                dish.calories ? `<div class="dish-preview__row"><span class="dish-preview__label">Калории</span><span class="dish-preview__value">${dish.calories} ккал</span></div>` : '',
                `<div class="dish-preview__row"><span class="dish-preview__label">Статус</span><span class="dish-preview__value">${dish.available ? 'В наличии' : 'Нет в наличии'}</span></div>`
            ].filter(Boolean).join('');

            const content = `
                <div class="modal__header">
                    <h3 class="modal__title">
                        <svg class="modal__title-icon" style="color: var(--mustard)" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><path d="M8 14s1.5 2 4 2 4-2 4-2"></path><line x1="9" y1="9" x2="9.01" y2="9"></line><line x1="15" y1="9" x2="15.01" y2="9"></line></svg>
                        ${dish.name}
                    </h3>
                    <button class="modal__close" data-action="close">${CLOSE_ICON}</button>
                </div>
                <div class="modal__body">
                    <div class="dish-preview">
                        ${dish.image ? `<img src="${dish.image}" alt="${dish.name}" class="dish-preview__image">` : ''}
                        <div class="dish-preview__info">${info}</div>
                        ${dish.description ? `<div class="dish-preview__description">${dish.description}</div>` : ''}
                    </div>
                </div>
                <div class="modal__footer">
                    <button class="btn btn--secondary" data-action="close">Закрыть</button>
                    <a href="/admin/dishes/${dish.id}/edit" class="btn btn--primary">Редактировать</a>
                </div>`;
            const modalEl = this.open(content, { large: true });
            modalEl.addEventListener('click', (e) => { if (e.target.closest('[data-action="close"]')) this.close(); });
        }

        form(options) {
            return new Promise((resolve) => {
                const modalEl = this.open(options.content, { large: options.large });
                const form = modalEl.querySelector('form');
                if (form) {
                    form.addEventListener('submit', (e) => {
                        e.preventDefault();
                        this.close();
                        resolve(Object.fromEntries(new FormData(form).entries()));
                    });
                }
                modalEl.addEventListener('click', (e) => {
                    const action = e.target.closest('[data-action]')?.dataset.action;
                    if (action === 'cancel' || action === 'close') { this.close(); resolve(null); }
                });
            });
        }
    }

    window.ModalManager = ModalManager;
})();
