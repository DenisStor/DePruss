/**
 * Base API Client
 * Provides unified fetch wrapper with error handling
 */
(function() {
    'use strict';

    class ApiClient {
        constructor(baseUrl = '') {
            this.baseUrl = baseUrl;
        }

        async request(endpoint, options = {}) {
            const url = this.baseUrl + endpoint;
            const config = {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            };

            if (config.body && typeof config.body === 'object') {
                config.body = JSON.stringify(config.body);
            }

            try {
                const response = await fetch(url, config);

                if (!response.ok) {
                    const error = await response.json().catch(() => ({}));
                    throw new Error(error.detail || `HTTP ${response.status}`);
                }

                return response.json();
            } catch (error) {
                console.error('API Error:', error);
                throw error;
            }
        }

        get(endpoint, options = {}) {
            return this.request(endpoint, { ...options, method: 'GET' });
        }

        post(endpoint, body, options = {}) {
            return this.request(endpoint, { ...options, method: 'POST', body });
        }

        patch(endpoint, body, options = {}) {
            return this.request(endpoint, { ...options, method: 'PATCH', body });
        }

        put(endpoint, body, options = {}) {
            return this.request(endpoint, { ...options, method: 'PUT', body });
        }

        delete(endpoint, options = {}) {
            return this.request(endpoint, { ...options, method: 'DELETE' });
        }
    }

    window.ApiClient = ApiClient;
})();
