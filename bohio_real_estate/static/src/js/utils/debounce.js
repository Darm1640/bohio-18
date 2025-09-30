/**
 * BOHIO Real Estate - Debounce Utility
 * Función para optimizar eventos repetitivos
 */

export const debounce = (func, delay = 300) => {
    let timeoutId;

    return function(...args) {
        clearTimeout(timeoutId);

        timeoutId = setTimeout(() => {
            func.apply(this, args);
        }, delay);
    };
};

export const throttle = (func, limit = 300) => {
    let inThrottle;

    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;

            setTimeout(() => {
                inThrottle = false;
            }, limit);
        }
    };
};