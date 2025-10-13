/** @odoo-module **/

// =============================================================================
// BOHIO REAL ESTATE - DOM HELPERS
// =============================================================================
// Utilidades genéricas para manipulación del DOM
// Reutilizables en toda la aplicación - Sin HTML strings

// -----------------------------------------------------------------------------
// SELECTORES Y VALIDACIÓN
// -----------------------------------------------------------------------------

/**
 * Busca un elemento validando que exista
 * @param {string} selector - Selector CSS
 * @param {HTMLElement} context - Contexto de búsqueda (default: document)
 * @returns {HTMLElement|null}
 */
export function getElement(selector, context = document) {
    return context.querySelector(selector);
}

/**
 * Busca múltiples elementos
 * @param {string} selector - Selector CSS
 * @param {HTMLElement} context - Contexto de búsqueda (default: document)
 * @returns {NodeList}
 */
export function getElements(selector, context = document) {
    return context.querySelectorAll(selector);
}

/**
 * Verifica si un elemento existe
 * @param {string} selector - Selector CSS
 * @param {HTMLElement} context - Contexto de búsqueda (default: document)
 * @returns {boolean}
 */
export function elementExists(selector, context = document) {
    return getElement(selector, context) !== null;
}

// -----------------------------------------------------------------------------
// CREACIÓN DE ELEMENTOS
// -----------------------------------------------------------------------------

/**
 * Crea un elemento con clase y contenido
 * @param {string} tag - Tag del elemento
 * @param {string|Array<string>} className - Clase o array de clases
 * @param {string} textContent - Contenido de texto (opcional)
 * @returns {HTMLElement}
 */
export function createElement(tag, className = '', textContent = '') {
    const element = document.createElement(tag);

    if (className) {
        if (Array.isArray(className)) {
            element.classList.add(...className);
        } else {
            element.className = className;
        }
    }

    if (textContent) {
        element.textContent = textContent;
    }

    return element;
}

/**
 * Crea un botón con icono Bootstrap
 * @param {Object} options - Opciones del botón
 * @param {string} options.text - Texto del botón
 * @param {string} options.icon - Clase del icono (ej: 'bi-search')
 * @param {string} options.className - Clases adicionales
 * @param {Function} options.onClick - Handler del click
 * @returns {HTMLButtonElement}
 */
export function createButton(options) {
    const button = createElement('button', options.className || 'btn');
    button.type = 'button';

    if (options.icon) {
        const icon = createElement('i', `bi ${options.icon}`);
        button.appendChild(icon);

        if (options.text) {
            button.appendChild(document.createTextNode(` ${options.text}`));
        }
    } else if (options.text) {
        button.textContent = options.text;
    }

    if (options.onClick) {
        button.addEventListener('click', options.onClick);
    }

    return button;
}

/**
 * Crea un link con icono Bootstrap
 * @param {Object} options - Opciones del link
 * @param {string} options.href - URL del link
 * @param {string} options.text - Texto del link
 * @param {string} options.icon - Clase del icono (ej: 'bi-house')
 * @param {string} options.className - Clases adicionales
 * @returns {HTMLAnchorElement}
 */
export function createLink(options) {
    const link = createElement('a', options.className || '');
    link.href = options.href;

    if (options.icon) {
        const icon = createElement('i', `bi ${options.icon}`);
        link.appendChild(icon);

        if (options.text) {
            link.appendChild(document.createTextNode(` ${options.text}`));
        }
    } else if (options.text) {
        link.textContent = options.text;
    }

    return link;
}

// -----------------------------------------------------------------------------
// MANIPULACIÓN DE ELEMENTOS
// -----------------------------------------------------------------------------

/**
 * Muestra un elemento
 * @param {HTMLElement|string} element - Elemento o selector
 */
export function showElement(element) {
    const el = typeof element === 'string' ? getElement(element) : element;
    if (el) el.style.display = '';
}

/**
 * Oculta un elemento
 * @param {HTMLElement|string} element - Elemento o selector
 */
export function hideElement(element) {
    const el = typeof element === 'string' ? getElement(element) : element;
    if (el) el.style.display = 'none';
}

/**
 * Toggle visibility de un elemento
 * @param {HTMLElement|string} element - Elemento o selector
 */
export function toggleElement(element) {
    const el = typeof element === 'string' ? getElement(element) : element;
    if (el) {
        el.style.display = el.style.display === 'none' ? '' : 'none';
    }
}

/**
 * Agrega clase(s) a un elemento
 * @param {HTMLElement|string} element - Elemento o selector
 * @param {string|Array<string>} className - Clase o array de clases
 */
export function addClass(element, className) {
    const el = typeof element === 'string' ? getElement(element) : element;
    if (el) {
        if (Array.isArray(className)) {
            el.classList.add(...className);
        } else {
            el.classList.add(className);
        }
    }
}

/**
 * Remueve clase(s) de un elemento
 * @param {HTMLElement|string} element - Elemento o selector
 * @param {string|Array<string>} className - Clase o array de clases
 */
export function removeClass(element, className) {
    const el = typeof element === 'string' ? getElement(element) : element;
    if (el) {
        if (Array.isArray(className)) {
            el.classList.remove(...className);
        } else {
            el.classList.remove(className);
        }
    }
}

/**
 * Toggle clase de un elemento
 * @param {HTMLElement|string} element - Elemento o selector
 * @param {string} className - Clase
 */
export function toggleClass(element, className) {
    const el = typeof element === 'string' ? getElement(element) : element;
    if (el) {
        el.classList.toggle(className);
    }
}

/**
 * Limpia el contenido de un elemento
 * @param {HTMLElement|string} element - Elemento o selector
 */
export function clearElement(element) {
    const el = typeof element === 'string' ? getElement(element) : element;
    if (el) {
        el.innerHTML = '';
    }
}

/**
 * Remueve un elemento del DOM
 * @param {HTMLElement|string} element - Elemento o selector
 */
export function removeElement(element) {
    const el = typeof element === 'string' ? getElement(element) : element;
    if (el && el.parentNode) {
        el.parentNode.removeChild(el);
    }
}

// -----------------------------------------------------------------------------
// EVENTOS
// -----------------------------------------------------------------------------

/**
 * Agrega event listener con validación
 * @param {HTMLElement|string} element - Elemento o selector
 * @param {string} event - Nombre del evento
 * @param {Function} handler - Handler del evento
 * @param {Object} options - Opciones del listener
 */
export function addEventListener(element, event, handler, options = {}) {
    const el = typeof element === 'string' ? getElement(element) : element;
    if (el) {
        el.addEventListener(event, handler, options);
    }
}

/**
 * Remueve event listener
 * @param {HTMLElement|string} element - Elemento o selector
 * @param {string} event - Nombre del evento
 * @param {Function} handler - Handler del evento
 */
export function removeEventListener(element, event, handler) {
    const el = typeof element === 'string' ? getElement(element) : element;
    if (el) {
        el.removeEventListener(event, handler);
    }
}

// -----------------------------------------------------------------------------
// ATRIBUTOS Y DATOS
// -----------------------------------------------------------------------------

/**
 * Obtiene atributo de un elemento
 * @param {HTMLElement|string} element - Elemento o selector
 * @param {string} attr - Nombre del atributo
 * @returns {string|null}
 */
export function getAttribute(element, attr) {
    const el = typeof element === 'string' ? getElement(element) : element;
    return el ? el.getAttribute(attr) : null;
}

/**
 * Establece atributo de un elemento
 * @param {HTMLElement|string} element - Elemento o selector
 * @param {string} attr - Nombre del atributo
 * @param {string} value - Valor del atributo
 */
export function setAttribute(element, attr, value) {
    const el = typeof element === 'string' ? getElement(element) : element;
    if (el) {
        el.setAttribute(attr, value);
    }
}

/**
 * Obtiene data attribute de un elemento
 * @param {HTMLElement|string} element - Elemento o selector
 * @param {string} key - Nombre del data attribute (sin 'data-')
 * @returns {string|null}
 */
export function getDataAttr(element, key) {
    const el = typeof element === 'string' ? getElement(element) : element;
    return el ? el.dataset[key] : null;
}

/**
 * Establece data attribute de un elemento
 * @param {HTMLElement|string} element - Elemento o selector
 * @param {string} key - Nombre del data attribute (sin 'data-')
 * @param {string} value - Valor
 */
export function setDataAttr(element, key, value) {
    const el = typeof element === 'string' ? getElement(element) : element;
    if (el) {
        el.dataset[key] = value;
    }
}

// -----------------------------------------------------------------------------
// LOADING Y ESTADOS
// -----------------------------------------------------------------------------

/**
 * Muestra loading en un elemento
 * @param {HTMLElement|string} element - Elemento o selector
 * @param {string} message - Mensaje opcional
 */
export function showLoading(element, message = 'Cargando...') {
    const el = typeof element === 'string' ? getElement(element) : element;
    if (!el) return;

    const loader = createElement('div', 'loading-overlay');

    const spinner = createElement('div', 'spinner-border text-danger');
    spinner.setAttribute('role', 'status');

    const span = createElement('span', 'visually-hidden', message);
    spinner.appendChild(span);

    loader.appendChild(spinner);

    if (message) {
        const text = createElement('p', 'mt-3', message);
        loader.appendChild(text);
    }

    el.appendChild(loader);
}

/**
 * Oculta loading de un elemento
 * @param {HTMLElement|string} element - Elemento o selector
 */
export function hideLoading(element) {
    const el = typeof element === 'string' ? getElement(element) : element;
    if (!el) return;

    const loader = el.querySelector('.loading-overlay');
    if (loader) {
        removeElement(loader);
    }
}

/**
 * Deshabilita un elemento (botón, input, etc.)
 * @param {HTMLElement|string} element - Elemento o selector
 */
export function disableElement(element) {
    const el = typeof element === 'string' ? getElement(element) : element;
    if (el) {
        el.disabled = true;
        addClass(el, 'disabled');
    }
}

/**
 * Habilita un elemento
 * @param {HTMLElement|string} element - Elemento o selector
 */
export function enableElement(element) {
    const el = typeof element === 'string' ? getElement(element) : element;
    if (el) {
        el.disabled = false;
        removeClass(el, 'disabled');
    }
}
