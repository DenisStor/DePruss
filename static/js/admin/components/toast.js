/**
 * Toast Notifications Manager
 * Displays temporary notification messages
 */
(function() {
    'use strict';

    const ICONS = {
        success: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>',
        error: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>',
        warning: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
        info: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>',
        undo: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 7v6h6"></path><path d="M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6 2.3L3 13"></path></svg>'
    };

    class ToastManager {
        constructor() {
            this.container = document.createElement('div');
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
            this.undoTimers = new Map();
        }

        show(type, title, message, options = {}) {
            const duration = options.duration !== undefined ? options.duration : 4000;
            const toast = document.createElement('div');
            toast.className = `toast toast--${type}`;
            toast.id = options.id || `toast-${Date.now()}`;

            toast.innerHTML = this._buildContent(type, title, message, options);
            this.container.appendChild(toast);

            this._bindClose(toast);

            if (options.onUndo) {
                return this._setupUndo(toast, options);
            }

            if (duration > 0) {
                setTimeout(() => this.hide(toast), duration);
            }
            return toast;
        }

        _buildContent(type, title, message, options) {
            let html = `
                <span class="toast__icon">${ICONS[type] || ICONS.info}</span>
                <div class="toast__content">
                    <div class="toast__title">${title}</div>
                    ${message ? `<div class="toast__message">${message}</div>` : ''}
                </div>
            `;

            if (options.onUndo) {
                html += `
                    <button class="toast__undo" data-action="undo">
                        Отменить
                        <span class="toast__countdown">${Math.ceil(options.undoTimeout / 1000) || 5}</span>
                    </button>
                `;
            }

            html += `
                <button class="toast__close" aria-label="Закрыть">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            `;

            return html;
        }

        _bindClose(toast) {
            const closeBtn = toast.querySelector('.toast__close');
            closeBtn.addEventListener('click', () => this.hide(toast));
        }

        _setupUndo(toast, options) {
            const undoBtn = toast.querySelector('.toast__undo');
            const countdown = toast.querySelector('.toast__countdown');
            const undoTimeout = options.undoTimeout || 5000;
            let remaining = undoTimeout;

            const countdownTimer = setInterval(() => {
                remaining -= 1000;
                if (countdown) countdown.textContent = Math.ceil(remaining / 1000);
                if (remaining <= 0) clearInterval(countdownTimer);
            }, 1000);

            this.undoTimers.set(toast.id, {
                countdown: countdownTimer,
                action: setTimeout(() => {
                    clearInterval(countdownTimer);
                    this.hide(toast);
                    if (options.onConfirm) options.onConfirm();
                }, undoTimeout)
            });

            undoBtn.addEventListener('click', () => {
                const timers = this.undoTimers.get(toast.id);
                if (timers) {
                    clearInterval(timers.countdown);
                    clearTimeout(timers.action);
                    this.undoTimers.delete(toast.id);
                }
                this.hide(toast);
                options.onUndo();
            });

            return toast;
        }

        hide(toast) {
            if (!toast.classList.contains('toast--hiding')) {
                toast.classList.add('toast--hiding');
                const timers = this.undoTimers.get(toast.id);
                if (timers) {
                    clearInterval(timers.countdown);
                    clearTimeout(timers.action);
                    this.undoTimers.delete(toast.id);
                }
                setTimeout(() => toast.remove(), 300);
            }
        }

        success(title, message, options = {}) { return this.show('success', title, message, options); }
        error(title, message, options = {}) { return this.show('error', title, message, options); }
        warning(title, message, options = {}) { return this.show('warning', title, message, options); }
        info(title, message, options = {}) { return this.show('info', title, message, options); }

        withUndo(title, message, options = {}) {
            return this.show('undo', title, message, { ...options, duration: 0 });
        }
    }

    window.ToastManager = ToastManager;
})();
