#!/usr/bin/env python3
"""
Script rápido para verificar y aplicar migraciones de OCR
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_chvs.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

django.setup()

print("="*60)
print("VERIFICACIÓN DE MIGRACIONES OCR")
print("="*60)

from django.core.management import call_command
from django.db import connection

# 1. Ver estado de migraciones
print("\n📋 Estado de migraciones de ocr_validation:")
call_command('showmigrations', 'ocr_validation')

# 2. Verificar si hay migraciones pendientes
print("\n🔍 Verificando migraciones pendientes...")
from django.db.migrations.executor import MigrationExecutor

executor = MigrationExecutor(connection)
plan = executor.migration_plan(executor.loader.graph.leaf_nodes())

if plan:
    print(f"   ⚠️  Hay {len(plan)} migraciones pendientes")
    print("\n¿Deseas aplicar las migraciones ahora? (s/n): ", end="")
    respuesta = input().strip().lower()

    if respuesta == 's':
        print("\n🔧 Aplicando migraciones...")
        call_command('migrate', 'ocr_validation')
        print("\n✅ Migraciones aplicadas exitosamente")
    else:
        print("\n⏭️  Migraciones no aplicadas. Ejecuta manualmente:")
        print("   python manage.py migrate ocr_validation")
else:
    print("   ✅ No hay migraciones pendientes")

# 3. Verificar que las tablas existen
print("\n📊 Verificando tablas en base de datos...")
from django.conf import settings

db_engine = settings.DATABASES['default']['ENGINE']

try:
    with connection.cursor() as cursor:
        if 'postgresql' in db_engine:
            cursor.execute("""
                SELECT tablename
                FROM pg_tables
                WHERE schemaname='public' AND tablename LIKE 'ocr_%'
                ORDER BY tablename;
            """)
        elif 'sqlite' in db_engine:
            cursor.execute("""
                SELECT name
                FROM sqlite_master
                WHERE type='table' AND name LIKE 'ocr_%'
                ORDER BY name;
            """)
        else:
            cursor.execute("SHOW TABLES LIKE 'ocr_%';")

        tablas = cursor.fetchall()

        if tablas:
            print(f"   ✅ Tablas OCR encontradas ({len(tablas)}):")
            for tabla in tablas:
                print(f"      - {tabla[0]}")
        else:
            print("   ❌ No se encontraron tablas OCR")
            print("   Ejecuta: python manage.py migrate ocr_validation")

except Exception as e:
    print(f"   ❌ Error verificando tablas: {e}")

# 4. Verificar configuración OCR
print("\n⚙️  Verificando configuración OCR...")
from ocr_validation.models import OCRConfiguration

try:
    config_count = OCRConfiguration.objects.count()
    if config_count > 0:
        config = OCRConfiguration.objects.first()
        print(f"   ✅ Configuración OCR existe:")
        print(f"      - Confianza mínima: {config.confianza_minima}%")
        print(f"      - Detectar firmas: {config.detectar_firmas}")
        print(f"      - Tesseract config: {config.tesseract_config}")
    else:
        print("   ⚠️  No existe configuración OCR")
        print("\n¿Deseas crear una configuración por defecto? (s/n): ", end="")
        respuesta = input().strip().lower()

        if respuesta == 's':
            config = OCRConfiguration.objects.create()
            print(f"   ✅ Configuración creada con ID: {config.id}")
        else:
            print("   ⏭️  Configuración no creada")
except Exception as e:
    print(f"   ❌ Error verificando configuración: {e}")

print("\n" + "="*60)
print("✅ VERIFICACIÓN COMPLETADA")
print("="*60)
