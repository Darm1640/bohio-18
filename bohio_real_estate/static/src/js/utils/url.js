/**
 * BOHIO Real Estate - URL Utilities
 * Funciones para manipulación de URLs y parámetros
 */

export const getUrlParams = () => {
    const params = new URLSearchParams(window.location.search);
    const result = {};

    for (const [key, value] of params) {
        result[key] = value;
    }

    return result;
};

export const getUrlParam = (paramName) => {
    const params = new URLSearchParams(window.location.search);
    return params.get(paramName);
};

export const setUrlParams = (params, pushState = true) => {
    const url = new URL(window.location);

    Object.entries(params).forEach(([key, value]) => {
        if (value === null || value === undefined || value === '') {
            url.searchParams.delete(key);
        } else {
            url.searchParams.set(key, value);
        }
    });

    if (pushState) {
        window.history.pushState({}, '', url);
    } else {
        window.history.replaceState({}, '', url);
    }
};

export const buildQueryString = (params) => {
    const filteredParams = Object.entries(params)
        .filter(([_, value]) => value !== null && value !== undefined && value !== '')
        .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
        .join('&');

    return filteredParams ? `?${filteredParams}` : '';
};

export const navigate = (path, params = {}) => {
    const queryString = buildQueryString(params);
    window.location.href = `${path}${queryString}`;
};