/**
 * BOHIO Real Estate - DOM Utilities
 * Funciones genéricas para manipulación del DOM
 */

export const $ = (selector, context = document) => {
    return context.querySelector(selector);
};

export const $$ = (selector, context = document) => {
    return Array.from(context.querySelectorAll(selector));
};

export const createElement = (tag, attributes = {}, children = []) => {
    const element = document.createElement(tag);

    Object.entries(attributes).forEach(([key, value]) => {
        if (key === 'className') {
            element.className = value;
        } else if (key === 'dataset') {
            Object.entries(value).forEach(([dataKey, dataValue]) => {
                element.dataset[dataKey] = dataValue;
            });
        } else if (key.startsWith('on')) {
            element.addEventListener(key.substring(2).toLowerCase(), value);
        } else {
            element.setAttribute(key, value);
        }
    });

    children.forEach(child => {
        if (typeof child === 'string') {
            element.appendChild(document.createTextNode(child));
        } else {
            element.appendChild(child);
        }
    });

    return element;
};

export const show = (element) => {
    if (element) element.style.display = '';
};

export const hide = (element) => {
    if (element) element.style.display = 'none';
};

export const toggle = (element) => {
    if (element) {
        element.style.display = element.style.display === 'none' ? '' : 'none';
    }
};

export const addClass = (element, className) => {
    if (element) element.classList.add(className);
};

export const removeClass = (element, className) => {
    if (element) element.classList.remove(className);
};

export const toggleClass = (element, className) => {
    if (element) element.classList.toggle(className);
};

export const hasClass = (element, className) => {
    return element ? element.classList.contains(className) : false;
};