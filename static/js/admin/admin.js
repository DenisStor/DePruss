/**
 * Admin Panel Initialization
 * Main entry point that initializes all modules
 */
(function() {
    'use strict';

    // ========================================
    // SIDEBAR TOGGLE
    // ========================================
    function initSidebar() {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('overlay');
        const menuToggle = document.getElementById('menuToggle');

        menuToggle?.addEventListener('click', () => {
            sidebar.classList.toggle('active');
            overlay.classList.toggle('active');
        });

        overlay?.addEventListener('click', () => {
            sidebar.classList.remove('active');
            overlay.classList.remove('active');
        });
    }

    // ========================================
    // FLASH MESSAGES FROM URL
    // ========================================
    function handleFlashMessages() {
        const params = new URLSearchParams(window.location.search);

        if (params.get('success')) {
            window.toast.success('Успешно', decodeURIComponent(params.get('success')));
            window.history.replaceState({}, '', window.location.pathname);
        }

        if (params.get('error')) {
            window.toast.error('Ошибка', decodeURIComponent(params.get('error')));
            window.history.replaceState({}, '', window.location.pathname);
        }
    }

    // ========================================
    // KEYBOARD HINT
    // ========================================
    function showKeyboardHint() {
        if (!localStorage.getItem('shortcuts_hint_shown')) {
            setTimeout(() => {
                window.toast.info('Подсказка', 'Нажмите ? для просмотра горячих клавиш', { duration: 6000 });
                localStorage.setItem('shortcuts_hint_shown', 'true');
            }, 2000);
        }
    }

    // ========================================
    // INITIALIZATION
    // ========================================
    document.addEventListener('DOMContentLoaded', () => {
        // Initialize sidebar toggle
        initSidebar();

        // Initialize toast manager
        window.toast = new ToastManager();

        // Initialize modal manager
        window.modal = new ModalManager();

        // Initialize keyboard shortcuts
        window.shortcuts = new KeyboardShortcuts();

        // Initialize table navigator if table exists
        const adminTable = document.querySelector('.table');
        if (adminTable) {
            window.tableNavigator = new TableNavigator({
                tableSelector: '.table',
                rowSelector: 'tbody tr[data-id]'
            });
        }

        // Handle flash messages from URL
        handleFlashMessages();

        // Show keyboard hint on first visit
        showKeyboardHint();

        // Initialize CountUp animations for dashboard
        if (document.querySelector('[data-count]') && window.initCountUpAnimations) {
            window.initCountUpAnimations();
        }

        // Initialize Activity Feed for dashboard
        if (document.getElementById('activityFeed')) {
            window.activityFeed = new ActivityFeed();
        }
    });
})();
