/** @odoo-module **/

import { jsonrpc } from "@web/core/network/rpc_service";

document.addEventListener('DOMContentLoaded', function() {

    const stateFilter = document.getElementById('state_filter');
    const cityFilter = document.getElementById('city_filter');
    const regionFilter = document.getElementById('region_filter');
    const searchByCodeBtn = document.getElementById('search_by_code_btn');
    const propertyCodeInput = document.getElementById('property_code_input');
    const codeSearchResult = document.getElementById('code_search_result');

    if (stateFilter && cityFilter) {
        stateFilter.addEventListener('change', async function() {
            const stateId = this.value;

            cityFilter.innerHTML = '<option value="">Ciudad</option>';
            regionFilter.innerHTML = '<option value="">Barrio</option>';

            if (stateId) {
                try {
                    const result = await jsonrpc('/api/cities_by_state', {
                        state_id: parseInt(stateId)
                    });

                    if (result.cities && result.cities.length > 0) {
                        result.cities.forEach(city => {
                            const option = document.createElement('option');
                            option.value = city.id;
                            option.textContent = city.name;
                            cityFilter.appendChild(option);
                        });
                    }
                } catch (error) {
                    console.error('Error loading cities:', error);
                }
            }
        });
    }

    if (cityFilter && regionFilter) {
        cityFilter.addEventListener('change', async function() {
            const cityId = this.value;
            const cityName = this.options[this.selectedIndex]?.text;

            regionFilter.innerHTML = '<option value="">Barrio</option>';

            if (cityId && cityName) {
                try {
                    const result = await jsonrpc('/api/regions_by_city', {
                        city_name: cityName
                    });

                    if (result.regions && result.regions.length > 0) {
                        result.regions.forEach(region => {
                            const option = document.createElement('option');
                            option.value = region.id;
                            option.textContent = region.name;
                            regionFilter.appendChild(option);
                        });
                    }
                } catch (error) {
                    console.error('Error loading regions:', error);
                }
            }
        });
    }

    if (searchByCodeBtn && propertyCodeInput && codeSearchResult) {
        searchByCodeBtn.addEventListener('click', async function() {
            const code = propertyCodeInput.value.trim();

            if (!code) {
                codeSearchResult.className = 'alert alert-warning';
                codeSearchResult.textContent = 'Por favor ingrese un código de propiedad';
                codeSearchResult.style.display = 'block';
                return;
            }

            searchByCodeBtn.disabled = true;
            searchByCodeBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Buscando...';

            try {
                const result = await jsonrpc('/api/properties/search_by_code', {
                    code: code
                });

                if (result.found) {
                    codeSearchResult.className = 'alert alert-success';
                    codeSearchResult.innerHTML = `
                        <strong>¡Propiedad encontrada!</strong><br>
                        <strong>${result.name}</strong> (${result.code})<br>
                        <a href="${result.url}" class="btn btn-sm btn-success mt-2">
                            Ver Propiedad
                        </a>
                    `;
                    codeSearchResult.style.display = 'block';
                } else {
                    codeSearchResult.className = 'alert alert-danger';
                    codeSearchResult.textContent = result.error || 'Propiedad no encontrada';
                    codeSearchResult.style.display = 'block';
                }
            } catch (error) {
                console.error('Error searching property:', error);
                codeSearchResult.className = 'alert alert-danger';
                codeSearchResult.textContent = 'Error al buscar la propiedad. Intente nuevamente.';
                codeSearchResult.style.display = 'block';
            } finally {
                searchByCodeBtn.disabled = false;
                searchByCodeBtn.innerHTML = '<i class="fa fa-search"></i> Buscar';
            }
        });

        propertyCodeInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                searchByCodeBtn.click();
            }
        });
    }

    const codeSearchModal = document.getElementById('codeSearchModal');
    if (codeSearchModal) {
        codeSearchModal.addEventListener('hidden.bs.modal', function () {
            propertyCodeInput.value = '';
            codeSearchResult.style.display = 'none';
        });
    }
});