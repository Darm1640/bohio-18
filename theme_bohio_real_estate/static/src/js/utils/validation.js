/**
 * BOHIO Real Estate - Validation Utilities
 * Funciones para validación de formularios
 */

export const isValidEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
};

export const isValidPhone = (phone) => {
    const phoneRegex = /^[\d\s\-\+\(\)]{7,15}$/;
    return phoneRegex.test(phone);
};

export const isValidColombiaCellPhone = (phone) => {
    const cleanPhone = phone.replace(/[\s\-\(\)]/g, '');
    return /^3\d{9}$/.test(cleanPhone);
};

export const isEmpty = (value) => {
    return value === null || value === undefined || value.toString().trim() === '';
};

export const isNumeric = (value) => {
    return !isNaN(parseFloat(value)) && isFinite(value);
};

export const validateForm = (formElement) => {
    const errors = [];
    const inputs = formElement.querySelectorAll('input[required], textarea[required], select[required]');

    inputs.forEach(input => {
        const value = input.value.trim();
        const label = input.previousElementSibling?.textContent || input.name;

        if (isEmpty(value)) {
            errors.push(`${label} es requerido`);
            input.classList.add('is-invalid');
        } else {
            input.classList.remove('is-invalid');

            if (input.type === 'email' && !isValidEmail(value)) {
                errors.push(`${label} no es válido`);
                input.classList.add('is-invalid');
            }

            if (input.type === 'tel' && !isValidPhone(value)) {
                errors.push(`${label} no es válido`);
                input.classList.add('is-invalid');
            }
        }
    });

    return {
        isValid: errors.length === 0,
        errors
    };
};