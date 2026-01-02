/**
 * Dashboard Utilities - CountUp animation and Activity Feed
 */
(function() {
    'use strict';

    class CountUp {
        constructor(element, options = {}) {
            this.element = element;
            this.endValue = Math.max(0, parseFloat(element.dataset.count || element.textContent) || 0);
            this.duration = options.duration || 1000;
            const match = element.textContent.match(/^(-?\d[\d\s,]*)(.*?)$/);
            this.textSuffix = match ? match[2] : '';
        }

        start() {
            const startTime = performance.now();
            const animate = (currentTime) => {
                const progress = Math.min((currentTime - startTime) / this.duration, 1);
                const easeOut = 1 - Math.pow(1 - progress, 3);
                const displayValue = Math.max(0, Math.round(this.endValue * easeOut));
                this.element.textContent = displayValue.toLocaleString('ru-RU') + this.textSuffix;
                if (progress < 1) requestAnimationFrame(animate);
            };
            requestAnimationFrame(animate);
        }
    }

    const ACTION_ICONS = {
        create: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>',
        update: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"></path></svg>',
        delete: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>',
        login: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"></path><polyline points="10 17 15 12 10 7"></polyline><line x1="15" y1="12" x2="3" y2="12"></line></svg>',
        logout: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>',
        default: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>'
    };

    class ActivityFeed {
        constructor(options = {}) {
            this.container = document.getElementById('activityFeed');
            this.periodSelect = document.getElementById('activityPeriod');
            this.apiEndpoint = options.apiEndpoint || '/admin/api/activity';
            if (this.container && this.periodSelect) this.init();
        }

        init() { this.periodSelect.addEventListener('change', () => this.loadActivity()); }

        async loadActivity() {
            this.showLoading();
            try {
                const response = await fetch(`${this.apiEndpoint}?period=${this.periodSelect.value}`);
                this.renderActivity((await response.json()).items);
            } catch (e) { console.error('Error loading activity:', e); window.toast?.error('Ошибка', 'Не удалось загрузить историю'); }
        }

        showLoading() {
            const skeleton = '<div class="skeleton-activity-item"><div class="skeleton skeleton-avatar"></div><div class="skeleton-content"><div class="skeleton skeleton-text" style="width:80%"></div><div class="skeleton skeleton-text" style="width:60%"></div></div></div>';
            this.container.innerHTML = `<div class="activity-feed__loading">${skeleton.repeat(5)}</div>`;
        }

        renderActivity(items) {
            if (!items.length) {
                this.container.innerHTML = '<div class="activity-empty"><svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line></svg><p>Нет активности за этот период</p></div>';
                return;
            }
            this.container.innerHTML = items.map((item, i) => `
                <div class="activity-item" style="animation-delay:${i * 0.05}s">
                    <div class="activity-item__icon activity-item__icon--${item.action}">${ACTION_ICONS[item.action] || ACTION_ICONS.default}</div>
                    <div class="activity-item__content">
                        <div class="activity-item__header">
                            <span class="activity-item__admin">${item.admin_username || 'Система'}</span>
                            <span class="activity-item__action-badge activity-item__action-badge--${item.action}">${item.action_display}</span>
                        </div>
                        <div class="activity-item__entity">${item.entity_type_display}: <strong>${item.entity_name || '—'}</strong></div>
                    </div>
                    <time class="activity-item__time">${this.formatTimeAgo(item.created_at)}</time>
                </div>`).join('');
        }

        formatTimeAgo(isoString) {
            if (!isoString) return '';
            const s = Math.floor((new Date() - new Date(isoString)) / 1000);
            if (s < 60) return 'сейчас';
            if (s < 3600) return `${Math.floor(s / 60)} мин.`;
            if (s < 86400) return `${Math.floor(s / 3600)} ч.`;
            if (s < 604800) return `${Math.floor(s / 86400)} дн.`;
            return new Date(isoString).toLocaleDateString('ru-RU');
        }
    }

    function initCountUpAnimations() {
        const elements = document.querySelectorAll('[data-count]');
        if (!elements.length) return;
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && !entry.target.dataset.animated) {
                    entry.target.dataset.animated = 'true';
                    new CountUp(entry.target).start();
                }
            });
        }, { threshold: 0.5 });
        elements.forEach(el => observer.observe(el));
    }

    window.CountUp = CountUp;
    window.ActivityFeed = ActivityFeed;
    window.initCountUpAnimations = initCountUpAnimations;
})();
