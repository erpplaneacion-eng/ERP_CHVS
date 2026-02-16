#!/usr/bin/env python
"""
Script para comparar el estado real de la base de datos con los modelos de Django.
Inspecciona tablas, columnas, índices y genera un reporte de diferencias.

Uso:
    python inspeccionar_db_vs_modelos.py
"""

import os
import sys
import django
from collections import defaultdict

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_chvs.settings')
django.setup()

from django.db import connection
from django.apps import apps


def get_db_tables():
    """Obtiene todas las tablas de la base de datos."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        return [row[0] for row in cursor.fetchall()]


def get_db_columns(table_name):
    """Obtiene todas las columnas de una tabla."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = %s
            ORDER BY ordinal_position;
        """, [table_name])
        return cursor.fetchall()


def get_db_indexes(table_name):
    """Obtiene todos los índices de una tabla."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                indexname,
                indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
            AND tablename = %s
            ORDER BY indexname;
        """, [table_name])
        return cursor.fetchall()


def get_db_constraints(table_name):
    """Obtiene todas las constraints de una tabla."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                con.conname AS constraint_name,
                con.contype AS constraint_type,
                CASE con.contype
                    WHEN 'p' THEN 'PRIMARY KEY'
                    WHEN 'f' THEN 'FOREIGN KEY'
                    WHEN 'u' THEN 'UNIQUE'
                    WHEN 'c' THEN 'CHECK'
                    ELSE con.contype::text
                END AS constraint_type_name
            FROM pg_constraint con
            JOIN pg_class rel ON rel.oid = con.conrelid
            JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
            WHERE nsp.nspname = 'public'
            AND rel.relname = %s
            ORDER BY con.conname;
        """, [table_name])
        return cursor.fetchall()


def inspect_facturacion_model():
    """Inspecciona específicamente el modelo ListadosFocalizacion."""
    print("\n" + "="*80)
    print("INSPECCIÓN DETALLADA: facturacion.ListadosFocalizacion")
    print("="*80)

    # Obtener el modelo
    try:
        model = apps.get_model('facturacion', 'ListadosFocalizacion')
    except LookupError:
        print("❌ Modelo ListadosFocalizacion no encontrado")
        return

    # Información del modelo
    print(f"\n📋 MODELO DJANGO:")
    print(f"  Nombre de tabla (Meta.db_table): {model._meta.db_table}")
    print(f"  Nombre app: {model._meta.app_label}")
    print(f"  Nombre modelo: {model._meta.object_name}")

    # Campos del modelo
    print(f"\n  Campos definidos en el modelo:")
    for field in model._meta.fields:
        db_column = getattr(field, 'db_column', None) or field.column
        print(f"    - {field.name:30} → DB column: {db_column:30} (tipo: {field.get_internal_type()})")

    # Índices del modelo
    print(f"\n  Índices definidos en el modelo:")
    if hasattr(model._meta, 'indexes') and model._meta.indexes:
        for idx in model._meta.indexes:
            idx_name = getattr(idx, 'name', 'AUTO')
            print(f"    - {idx_name:40} → campos: {idx.fields}")
    else:
        print(f"    (Sin índices definidos)")

    # Verificar qué tabla existe en la BD
    print(f"\n🗄️  BASE DE DATOS:")
    db_tables = get_db_tables()

    # Buscar variaciones del nombre de tabla
    possible_names = [
        'facturacion_listados_focalizacion',
        'facturacion_Listados_Focalizacion',
        'Facturacion_Listados_Focalizacion',
    ]

    table_found = None
    for name in possible_names:
        if name in db_tables:
            table_found = name
            break

    if table_found:
        print(f"  ✅ Tabla encontrada: {table_found}")

        # Columnas en la BD
        print(f"\n  Columnas en la base de datos:")
        db_columns = get_db_columns(table_found)
        for col_name, data_type, is_nullable, default in db_columns:
            nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
            print(f"    - {col_name:30} {data_type:20} {nullable:10} {default or ''}")

        # Índices en la BD
        print(f"\n  Índices en la base de datos:")
        db_indexes = get_db_indexes(table_found)
        for idx_name, idx_def in db_indexes:
            print(f"    - {idx_name}")
            print(f"      {idx_def}")

        # Constraints en la BD
        print(f"\n  Constraints en la base de datos:")
        db_constraints = get_db_constraints(table_found)
        for const_name, const_type, const_type_name in db_constraints:
            print(f"    - {const_name:50} ({const_type_name})")

        # Comparación
        print(f"\n⚖️  COMPARACIÓN:")

        # Comparar columnas
        model_columns = {field.column: field for field in model._meta.fields}
        db_column_names = {col[0] for col in db_columns}

        missing_in_db = set(model_columns.keys()) - db_column_names
        missing_in_model = db_column_names - set(model_columns.keys())

        if missing_in_db:
            print(f"\n  ⚠️  Columnas en MODELO pero NO en BD:")
            for col in missing_in_db:
                print(f"    - {col}")

        if missing_in_model:
            print(f"\n  ⚠️  Columnas en BD pero NO en MODELO:")
            for col in missing_in_model:
                print(f"    - {col}")

        if not missing_in_db and not missing_in_model:
            print(f"\n  ✅ Todas las columnas coinciden entre modelo y BD")

        # Comparar índices
        model_index_names = {idx.name for idx in model._meta.indexes if hasattr(idx, 'name')}
        db_index_names = {idx[0] for idx in db_indexes}

        print(f"\n  📊 Índices:")
        print(f"    Modelo define: {model_index_names or 'Ninguno con nombre explícito'}")
        print(f"    BD tiene: {db_index_names}")

    else:
        print(f"  ❌ Tabla NO encontrada en la base de datos")
        print(f"  Tablas disponibles que empiezan con 'facturacion':")
        for table in sorted(db_tables):
            if table.startswith('facturacion'):
                print(f"    - {table}")


def inspect_nutricion_model():
    """Inspecciona el modelo RequerimientoSemanal de nutrición."""
    print("\n" + "="*80)
    print("INSPECCIÓN DETALLADA: nutricion.RequerimientoSemanal")
    print("="*80)

    try:
        model = apps.get_model('nutricion', 'RequerimientoSemanal')
    except LookupError:
        print("❌ Modelo RequerimientoSemanal no encontrado")
        return

    print(f"\n📋 MODELO DJANGO:")
    print(f"  Nombre de tabla: {model._meta.db_table}")

    print(f"\n  Campos ForeignKey:")
    for field in model._meta.fields:
        if field.get_internal_type() == 'ForeignKey':
            db_column = getattr(field, 'db_column', None) or field.column
            print(f"    - {field.name:20} → DB column: {db_column:30}")

    # Verificar tabla en BD
    print(f"\n🗄️  BASE DE DATOS:")
    table_name = model._meta.db_table
    db_tables = get_db_tables()

    if table_name in db_tables:
        print(f"  ✅ Tabla encontrada: {table_name}")

        print(f"\n  Columnas en la base de datos:")
        db_columns = get_db_columns(table_name)
        for col_name, data_type, is_nullable, default in db_columns:
            nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
            print(f"    - {col_name:30} {data_type:20} {nullable}")
    else:
        print(f"  ❌ Tabla NO encontrada: {table_name}")


def main():
    print("🔍 INSPECCIÓN DE BASE DE DATOS VS MODELOS DJANGO")
    print("="*80)

    # Información de conexión
    print(f"\nBase de datos: {connection.settings_dict['NAME']}")
    print(f"Host: {connection.settings_dict['HOST']}")
    print(f"Puerto: {connection.settings_dict['PORT']}")
    print(f"Usuario: {connection.settings_dict['USER']}")

    # Inspeccionar modelos específicos
    inspect_facturacion_model()
    inspect_nutricion_model()

    print("\n" + "="*80)
    print("✅ Inspección completada")
    print("="*80)


if __name__ == '__main__':
    main()
