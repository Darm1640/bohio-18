/**
 * BOHIO Real Estate - Contact Form
 * Formulario de contacto con validación
 */

import { $, addClass, removeClass } from '../utils/dom.js';
import { validateForm, isValidEmail, isValidColombiaCellPhone } from '../utils/validation.js';

class ContactForm {
    constructor(formSelector) {
        this.form = $(formSelector);
        this.init();
    }

    init() {
        if (!this.form) return;

        this.attachEvents();
    }

    attachEvents() {
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSubmit();
        });

        const emailInput = $('input[type="email"]', this.form);
        if (emailInput) {
            emailInput.addEventListener('blur', () => {
                this.validateEmail(emailInput);
            });
        }

        const phoneInput = $('input[type="tel"]', this.form);
        if (phoneInput) {
            phoneInput.addEventListener('blur', () => {
                this.validatePhone(phoneInput);
            });
        }
    }

    validateEmail(input) {
        const value = input.value.trim();

        if (value && !isValidEmail(value)) {
            addClass(input, 'is-invalid');
            this.showError(input, 'Email no válido');
            return false;
        } else {
            removeClass(input, 'is-invalid');
            this.hideError(input);
            return true;
        }
    }

    validatePhone(input) {
        const value = input.value.trim();

        if (value && !isValidColombiaCellPhone(value)) {
            addClass(input, 'is-invalid');
            this.showError(input, 'Teléfono celular colombiano no válido (debe iniciar con 3)');
            return false;
        } else {
            removeClass(input, 'is-invalid');
            this.hideError(input);
            return true;
        }
    }

    showError(input, message) {
        let errorDiv = input.nextElementSibling;

        if (!errorDiv || !errorDiv.classList.contains('invalid-feedback')) {
            errorDiv = document.createElement('div');
            errorDiv.className = 'invalid-feedback';
            input.parentNode.insertBefore(errorDiv, input.nextSibling);
        }

        errorDiv.textContent = message;
    }

    hideError(input) {
        const errorDiv = input.nextElementSibling;

        if (errorDiv && errorDiv.classList.contains('invalid-feedback')) {
            errorDiv.remove();
        }
    }

    async handleSubmit() {
        const validation = validateForm(this.form);

        if (!validation.isValid) {
            alert(validation.errors.join('\n'));
            return;
        }

        const submitBtn = $('button[type="submit"]', this.form);
        const originalText = submitBtn.textContent;

        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Enviando...';

        try {
            this.form.submit();
        } catch (error) {
            console.error('Error al enviar formulario:', error);
            alert('Error al enviar el formulario. Intente nuevamente.');
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new ContactForm('#contact-form');
    new ContactForm('#property-inquiry-form');
    new ContactForm('#pqrs-form');
});