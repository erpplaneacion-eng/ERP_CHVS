"""
Django management command para inspeccionar la estructura de la base de datos.

Uso:
    python manage.py inspeccionar_db                    # Ver todas las tablas
    python manage.py inspeccionar_db --app nutricion    # Ver solo tablas de una app
    python manage.py inspeccionar_db --tabla TablaMenus # Ver detalles de una tabla específica
    python manage.py inspeccionar_db --relaciones       # Ver relaciones ForeignKey
"""

from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import connection
from django.db.models import ForeignKey, ManyToManyField


class Command(BaseCommand):
    help = 'Inspecciona la estructura de las tablas en la base de datos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--app',
            type=str,
            help='Filtrar por app específica (ej: nutricion, principal, facturacion)'
        )
        parser.add_argument(
            '--tabla',
            type=str,
            help='Mostrar detalles de una tabla específica'
        )
        parser.add_argument(
            '--relaciones',
            action='store_true',
            help='Mostrar solo las relaciones ForeignKey y ManyToMany'
        )
        parser.add_argument(
            '--sql',
            action='store_true',
            help='Mostrar también la consulta SQL directa a la base de datos'
        )

    def handle(self, *args, **options):
        app_filter = options.get('app')
        tabla_filter = options.get('tabla')
        mostrar_relaciones = options.get('relaciones')
        mostrar_sql = options.get('sql')

        if tabla_filter:
            self.mostrar_detalle_tabla(tabla_filter)
        elif mostrar_relaciones:
            self.mostrar_relaciones()
        else:
            self.listar_tablas(app_filter, mostrar_sql)

    def listar_tablas(self, app_filter=None, mostrar_sql=False):
        """Lista todas las tablas con sus columnas"""
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 100))
        self.stdout.write(self.style.SUCCESS('INSPECCIÓN DE BASE DE DATOS - ERP_CHVS'))
        self.stdout.write(self.style.SUCCESS('=' * 100 + '\n'))

        for model in apps.get_models():
            app_label = model._meta.app_label

            # Filtrar por app si se especificó
            if app_filter and app_label != app_filter:
                continue

            tabla = model._meta.db_table
            modelo = model.__name__

            self.stdout.write(self.style.WARNING(f'\n📋 {app_label.upper()}.{modelo}'))
            self.stdout.write(f'   Tabla DB: {tabla}')
            self.stdout.write('-' * 100)

            # Información de campos
            self.stdout.write(f'{"Campo":<30} {"Tipo":<25} {"Null":<6} {"Detalles":<40}')
            self.stdout.write('-' * 100)

            for field in model._meta.get_fields():
                if hasattr(field, 'column'):
                    nombre_campo = field.name
                    tipo_campo = field.get_internal_type()
                    null = 'Sí' if field.null else 'No'

                    detalles = []

                    # ForeignKey
                    if isinstance(field, ForeignKey):
                        related_model = field.related_model.__name__
                        detalles.append(f'FK → {related_model}')
                        if field.on_delete:
                            detalles.append(f'on_delete={field.on_delete.__name__}')

                    # ManyToMany
                    elif isinstance(field, ManyToManyField):
                        related_model = field.related_model.__name__
                        detalles.append(f'M2M → {related_model}')

                    # CharField/TextField
                    elif hasattr(field, 'max_length') and field.max_length:
                        detalles.append(f'max_length={field.max_length}')

                    # DecimalField
                    elif hasattr(field, 'max_digits') and field.max_digits:
                        detalles.append(f'max_digits={field.max_digits}, decimal_places={field.decimal_places}')

                    # Default value
                    if hasattr(field, 'default') and field.default is not None and field.default != '':
                        if callable(field.default):
                            detalles.append(f'default=<function>')
                        else:
                            detalles.append(f'default={field.default}')

                    # Unique
                    if hasattr(field, 'unique') and field.unique:
                        detalles.append('UNIQUE')

                    # Primary Key
                    if hasattr(field, 'primary_key') and field.primary_key:
                        detalles.append('PRIMARY KEY')

                    detalles_str = ', '.join(detalles) if detalles else '-'

                    self.stdout.write(f'{nombre_campo:<30} {tipo_campo:<25} {null:<6} {detalles_str:<40}')

            # Contar registros
            try:
                count = model.objects.count()
                self.stdout.write(self.style.SUCCESS(f'\n✓ Total de registros: {count}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'\n✗ Error al contar registros: {str(e)}'))

        # Mostrar SQL directo si se solicitó
        if mostrar_sql:
            self.mostrar_tablas_sql()

    def mostrar_detalle_tabla(self, nombre_tabla):
        """Muestra detalles específicos de una tabla"""
        self.stdout.write(self.style.SUCCESS(f'\n{"=" * 100}'))
        self.stdout.write(self.style.SUCCESS(f'DETALLE DE TABLA: {nombre_tabla}'))
        self.stdout.write(self.style.SUCCESS(f'{"=" * 100}\n'))

        # Buscar el modelo
        modelo_encontrado = None
        for model in apps.get_models():
            if model.__name__.lower() == nombre_tabla.lower() or model._meta.db_table.lower() == nombre_tabla.lower():
                modelo_encontrado = model
                break

        if not modelo_encontrado:
            self.stdout.write(self.style.ERROR(f'✗ No se encontró el modelo/tabla: {nombre_tabla}'))
            self.stdout.write('\nTablas disponibles:')
            for model in apps.get_models():
                self.stdout.write(f'  - {model.__name__} (tabla: {model._meta.db_table})')
            return

        # Mostrar información detallada
        self.stdout.write(f'Modelo: {modelo_encontrado.__name__}')
        self.stdout.write(f'App: {modelo_encontrado._meta.app_label}')
        self.stdout.write(f'Tabla DB: {modelo_encontrado._meta.db_table}')
        self.stdout.write(f'Verbose Name: {modelo_encontrado._meta.verbose_name}')

        # Campos
        self.stdout.write(f'\n{"CAMPOS":-^100}')
        for field in modelo_encontrado._meta.get_fields():
            if hasattr(field, 'column'):
                self.stdout.write(f'\n  • {field.name}')
                self.stdout.write(f'    Tipo: {field.get_internal_type()}')
                self.stdout.write(f'    Columna DB: {field.column}')
                self.stdout.write(f'    Null: {field.null}')
                self.stdout.write(f'    Blank: {field.blank}')

                if isinstance(field, ForeignKey):
                    self.stdout.write(f'    Relación: ForeignKey → {field.related_model.__name__}')
                elif isinstance(field, ManyToManyField):
                    self.stdout.write(f'    Relación: ManyToManyField → {field.related_model.__name__}')

        # Índices
        if modelo_encontrado._meta.indexes:
            self.stdout.write(f'\n{"ÍNDICES":-^100}')
            for index in modelo_encontrado._meta.indexes:
                self.stdout.write(f'  • {index.name}: {index.fields}')

        # Unique together
        if modelo_encontrado._meta.unique_together:
            self.stdout.write(f'\n{"UNIQUE TOGETHER":-^100}')
            for unique in modelo_encontrado._meta.unique_together:
                self.stdout.write(f'  • {unique}')

        # Contar registros
        try:
            count = modelo_encontrado.objects.count()
            self.stdout.write(self.style.SUCCESS(f'\n✓ Total de registros en la tabla: {count}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Error al contar registros: {str(e)}'))

        # Mostrar primeros 5 registros (solo IDs y campos principales)
        try:
            primeros = modelo_encontrado.objects.all()[:5]
            if primeros:
                self.stdout.write(f'\n{"PRIMEROS 5 REGISTROS (muestra)":-^100}')
                for obj in primeros:
                    self.stdout.write(f'  {obj}')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'\n⚠ No se pudieron mostrar registros: {str(e)}'))

    def mostrar_relaciones(self):
        """Muestra solo las relaciones ForeignKey y ManyToMany"""
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 100))
        self.stdout.write(self.style.SUCCESS('RELACIONES EN LA BASE DE DATOS'))
        self.stdout.write(self.style.SUCCESS('=' * 100 + '\n'))

        for model in apps.get_models():
            relaciones_fk = []
            relaciones_m2m = []

            for field in model._meta.get_fields():
                if isinstance(field, ForeignKey):
                    relaciones_fk.append({
                        'campo': field.name,
                        'relacionado': field.related_model.__name__,
                        'on_delete': field.on_delete.__name__ if field.on_delete else 'N/A'
                    })
                elif isinstance(field, ManyToManyField):
                    relaciones_m2m.append({
                        'campo': field.name,
                        'relacionado': field.related_model.__name__
                    })

            if relaciones_fk or relaciones_m2m:
                self.stdout.write(self.style.WARNING(f'\n📦 {model._meta.app_label}.{model.__name__}'))

                if relaciones_fk:
                    self.stdout.write('  ForeignKeys:')
                    for rel in relaciones_fk:
                        self.stdout.write(f'    • {rel["campo"]} → {rel["relacionado"]} (on_delete={rel["on_delete"]})')

                if relaciones_m2m:
                    self.stdout.write('  ManyToMany:')
                    for rel in relaciones_m2m:
                        self.stdout.write(f'    • {rel["campo"]} ↔ {rel["relacionado"]}')

    def mostrar_tablas_sql(self):
        """Muestra las tablas usando SQL directo"""
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 100))
        self.stdout.write(self.style.SUCCESS('TABLAS EN LA BASE DE DATOS (Consulta SQL directa)'))
        self.stdout.write(self.style.SUCCESS('=' * 100 + '\n'))

        with connection.cursor() as cursor:
            # PostgreSQL query para listar tablas
            cursor.execute("""
                SELECT
                    schemaname,
                    tablename,
                    tableowner
                FROM pg_catalog.pg_tables
                WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                ORDER BY tablename;
            """)

            self.stdout.write(f'{"Schema":<20} {"Tabla":<50} {"Owner":<20}')
            self.stdout.write('-' * 100)

            for row in cursor.fetchall():
                self.stdout.write(f'{row[0]:<20} {row[1]:<50} {row[2]:<20}')

            # Contar total de tablas
            cursor.execute("""
                SELECT COUNT(*)
                FROM pg_catalog.pg_tables
                WHERE schemaname NOT IN ('pg_catalog', 'information_schema');
            """)
            total = cursor.fetchone()[0]
            self.stdout.write(self.style.SUCCESS(f'\n✓ Total de tablas: {total}'))
