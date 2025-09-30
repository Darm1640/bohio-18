/**
 * BOHIO Real Estate - API Utilities
 * Funciones genéricas para llamadas a APIs
 */

export const jsonRPC = (url, params = {}) => {
    return fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            jsonrpc: '2.0',
            method: 'call',
            params: params,
            id: new Date().getTime(),
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error.message || 'RPC Error');
        }
        return data.result;
    });
};

export const searchProperties = (filters = {}, page = 1, limit = 12) => {
    return jsonRPC('/api/properties/search', { filters, page, limit });
};

export const searchByCode = (code) => {
    return jsonRPC('/api/properties/search_by_code', { code });
};

export const locationAutocomplete = (term) => {
    return jsonRPC('/api/location/autocomplete', { term });
};

export const getCitiesByState = (stateId) => {
    return jsonRPC('/api/cities_by_state', { state_id: stateId });
};

export const getRegionsByCity = (cityName) => {
    return jsonRPC('/api/regions_by_city', { city_name: cityName });
};