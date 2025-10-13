// Script de Debug para Homepage
// Copiar y pegar en la consola del navegador (F12 → Console)

console.log('=== DEBUG HOMEPAGE BOHIO ===');

// 1. Verificar que los contenedores existen
console.log('\n[1] VERIFICANDO CONTENEDORES HTML:');
const containers = [
    'arriendo-properties-grid',
    'arriendo-properties-map',
    'used-sale-properties-grid',
    'used-sale-properties-map',
    'projects-properties-grid',
    'projects-properties-map'
];

containers.forEach(id => {
    const el = document.getElementById(id);
    console.log(`  ${id}: ${el ? '✅ EXISTE' : '❌ NO EXISTE'}`);
    if (el) {
        console.log(`    - innerHTML.length: ${el.innerHTML.length}`);
        console.log(`    - children.length: ${el.children.length}`);
    }
});

// 2. Verificar si el módulo RPC está disponible
console.log('\n[2] VERIFICANDO RPC:');
if (typeof odoo !== 'undefined') {
    console.log('  ✅ odoo está definido');
    if (odoo.define) {
        console.log('  ✅ odoo.define está disponible');
    }
} else {
    console.log('  ❌ odoo NO está definido');
}

// 3. Verificar si window.bohioHomepage existe
console.log('\n[3] VERIFICANDO window.bohioHomepage:');
if (typeof window.bohioHomepage !== 'undefined') {
    console.log('  ✅ window.bohioHomepage está definido');
    console.log('  Funciones disponibles:', Object.keys(window.bohioHomepage));
} else {
    console.log('  ❌ window.bohioHomepage NO está definido');
    console.log('  → El JavaScript homepage_properties.js NO se ejecutó');
}

// 4. Probar endpoint manualmente
console.log('\n[4] PROBANDO ENDPOINT MANUALMENTE:');
console.log('  Ejecutando fetch a /property/search/ajax...');

fetch('/property/search/ajax', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        jsonrpc: "2.0",
        method: "call",
        params: {
            context: "public",
            filters: {
                type_service: "rent",
                limit: 4
            },
            page: 1,
            ppg: 20,
            order: "newest"
        }
    })
})
.then(res => res.json())
.then(data => {
    console.log('\n[RESULTADO DEL TEST]:');
    if (data.result) {
        console.log('  ✅ Endpoint funciona correctamente');
        console.log(`  Total propiedades: ${data.result.total}`);
        console.log(`  Propiedades retornadas: ${data.result.properties.length}`);

        if (data.result.properties.length > 0) {
            console.log('\n  Muestra de propiedad:');
            const prop = data.result.properties[0];
            console.log('    ID:', prop.id);
            console.log('    Nombre:', prop.name);
            console.log('    Precio:', prop.price);
            console.log('    Ciudad:', prop.city);
        }
    } else if (data.error) {
        console.error('  ❌ Error del servidor:', data.error.message);
        console.error('  Detalles:', data.error);
    }
})
.catch(err => {
    console.error('  ❌ Error de red:', err);
});

// 5. Verificar errores en consola
console.log('\n[5] INSTRUCCIONES:');
console.log('  1. Revisa arriba si los contenedores HTML existen');
console.log('  2. Revisa si window.bohioHomepage está definido');
console.log('  3. Revisa el resultado del test del endpoint');
console.log('  4. Si window.bohioHomepage NO está definido:');
console.log('     → El archivo homepage_properties.js NO se cargó');
console.log('     → Ir a Network tab y buscar "homepage_properties.js"');
console.log('  5. Si el endpoint falla:');
console.log('     → Hay un problema en el servidor');
console.log('  6. Si todo funciona pero la página está vacía:');
console.log('     → Hay un error silencioso en el JavaScript');

console.log('\n=== FIN DEBUG ===');
