# Script para poblar las tablas GruposAlimentos y ComponentesAlimentos
# Para ejecutarlo, usa el shell de Django:
# python manage.py shell < poblar_datos_nutricion.py

from nutricion.models import GruposAlimentos, ComponentesAlimentos

def populate_data():
    # Datos para GruposAlimentos
    grupos_data = [
        ('g1', 'Grupo I. Cereales, raíces, tubérculos y plátanos'),
        ('g2', 'Grupo II. Fruta y verduras'),
        ('g3', 'Grupo III. Leche y productos lácteos'),
        ('g4', 'Grupo IV. Carnes, huevos, leguminosas secas, frutos secos y semillas'),
        ('g5', 'Grupo V. Grasas'),
        ('g6', 'Grupo VI. Azúcares'),
    ]

    for id_grupo, grupo_nombre in grupos_data:
        obj, created = GruposAlimentos.objects.get_or_create(id_grupo_alimentos=id_grupo, defaults={'grupo_alimentos': grupo_nombre})
        if created:
            print(f"Creado grupo: {obj.grupo_alimentos}")
        else:
            print(f"Grupo ya existe: {obj.grupo_alimentos}")


    print("Grupos de alimentos poblados.")

    # Datos para ComponentesAlimentos
    componentes_data = [
        ('com1', 'Bebida con leche', 'g3'),
        ('com2', 'Alimento proteico', 'g4'),
        ('com3', 'Cereal acompañante', 'g1'),
        ('com4', 'Fruta', 'g2'),
        ('com5', 'Azúcares', 'g6'),
        ('com6', 'Grasas', 'g5'),
        ('com7', 'Cereales', 'g1'),
        ('com8', 'Tuberculos, raíces, plátanos y derivados de cereal', 'g1'),
        ('com9', 'Ensalada o verdura caliente', 'g2'),
        ('com10', 'Bebida láctea y productos lácteos', 'g3'),
        ('com11', 'Leche y productos lácteos', 'g3'),
        ('com12', 'Frutas', 'g2'),
        ('com13', 'Postre', 'g4'),
    ]

    for id_comp, comp_nombre, id_grupo in componentes_data:
        try:
            grupo = GruposAlimentos.objects.get(id_grupo_alimentos=id_grupo)
            obj, created = ComponentesAlimentos.objects.get_or_create(id_componente=id_comp, defaults={'componente': comp_nombre, 'id_grupo_alimentos': grupo})
            if created:
                print(f"Creado componente: {obj.componente}")
            else:
                print(f"Componente ya existe: {obj.componente}")
        except GruposAlimentos.DoesNotExist:
            print(f"ERROR: El grupo con id={id_grupo} no existe. No se pudo crear el componente {comp_nombre}")


    print("Componentes de alimentos poblados.")

print("Ejecutando script de población de datos...")
populate_data()
print("Script finalizado.")