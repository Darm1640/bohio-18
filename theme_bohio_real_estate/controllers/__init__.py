# -*- coding: utf-8 -*-
"""
BOHIO Real Estate Controllers - Estructura Consolidada
======================================================
SOLO 3 controladores optimizados:

1. main.py                  - Homepage, proyectos, APIs generales, mapas, banners (38 rutas)
2. property_search.py       - Búsqueda avanzada, filtros, comparación (16 rutas)
3. property_interactions.py - Wishlist, mapas individuales (8 rutas)

Total: 62 rutas distribuidas en 3 archivos (~4,200 líneas)

ELIMINADOS (fusionados):
- mejoras_controller.py → main.py
- map_controller.py → main.py
- property_banner.py → main.py
- property_map_controller.py → property_interactions.py
- property_wishlist.py → renombrado a property_interactions.py
"""

from . import main
from . import property_search
from . import property_interactions
