import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_chvs.settings')
django.setup()

from nutricion.models import TablaMenus, TablaPreparaciones

# Buscar específicamente el menú 364
menus = TablaMenus.objects.filter(id_menu__in=[364, 365])

print("-" * 50)
for menu in menus:
    print(f"MENU: {menu.menu} (ID: {menu.id_menu})")
    print(f"Modalidad: {menu.id_modalidad.modalidad}")
    
    preps = TablaPreparaciones.objects.filter(id_menu=menu)
    
    if preps.count() == 0:
        print("  ⚠️  No tiene preparaciones creadas.")
    else:
        for p in preps:
            estado = "✅" if p.id_componente else "❌ SIN ASIGNAR"
            nombre_comp = p.id_componente.componente if p.id_componente else "---"
            print(f"  {estado} Prep: '{p.preparacion}' -> Componente: {nombre_comp}")
    print("-" * 50)
