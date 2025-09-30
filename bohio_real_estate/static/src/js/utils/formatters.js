/**
 * BOHIO Real Estate - Formatters Utilities
 * Funciones para formateo de datos
 */

export const formatCurrency = (value, currency = 'COP') => {
    if (value === null || value === undefined) return '';

    return new Intl.NumberFormat('es-CO', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(value);
};

export const formatNumber = (value) => {
    if (value === null || value === undefined) return '';

    return new Intl.NumberFormat('es-CO').format(value);
};

export const formatArea = (value, unit = 'm²') => {
    if (value === null || value === undefined) return '';

    const unitSymbol = {
        'm': 'm²',
        'yard': 'yd²',
        'hectare': 'ha'
    }[unit] || unit;

    return `${formatNumber(value)} ${unitSymbol}`;
};

export const formatDate = (dateString) => {
    if (!dateString) return '';

    const date = new Date(dateString);
    return new Intl.DateTimeFormat('es-CO', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    }).format(date);
};

export const truncateText = (text, maxLength = 100) => {
    if (!text) return '';
    if (text.length <= maxLength) return text;

    return text.substring(0, maxLength).trim() + '...';
};

export const slugify = (text) => {
    return text
        .toString()
        .toLowerCase()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .replace(/\s+/g, '-')
        .replace(/[^\w\-]+/g, '')
        .replace(/\-\-+/g, '-')
        .replace(/^-+/, '')
        .replace(/-+$/, '');
};