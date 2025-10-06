/** @odoo-module **/

/**
 * Homepage Landing - Bohío Real Estate
 * Funcionalidad para tabs Arrendar/Comprar
 */

export class HomepageLanding {
    constructor() {
        this.init();
    }

    init() {
        this.bindTabEvents();
    }

    bindTabEvents() {
        const tabArr = document.getElementById('tabArr');
        const tabComp = document.getElementById('tabComp');
        const searchType = document.getElementById('searchType');

        if (!tabArr || !tabComp || !searchType) return;

        tabArr.addEventListener('click', () => {
            this.setActiveTab(tabArr, tabComp, 'rent', searchType);
        });

        tabComp.addEventListener('click', () => {
            this.setActiveTab(tabComp, tabArr, 'sale', searchType);
        });
    }

    setActiveTab(activeBtn, inactiveBtn, type, searchTypeInput) {
        activeBtn.classList.add('active');
        inactiveBtn.classList.remove('active');
        searchTypeInput.value = type;
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('.bohio_homepage_landing')) {
        new HomepageLanding();
    }
});
