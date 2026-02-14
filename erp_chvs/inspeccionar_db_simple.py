#!/usr/bin/env python3
"""
Script simple para inspeccionar la base de datos PostgreSQL.
No requiere Django, solo psycopg2 y python-dotenv.

Uso:
    python3 inspeccionar_db_simple.py                    # Ver todas las tablas
    python3 inspeccionar_db_simple.py nutricion          # Ver tablas que contengan 'nutricion'
    python3 inspeccionar_db_simple.py --tabla nombre     # Ver detalles de una tabla específica
"""

import sys
import os
from pathlib import Path

# Cargar variables de entorno
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠ python-dotenv no instalado. Usando valores por defecto.")

# Configuración de la base de datos desde .env
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'erp_chvs'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'chvs2025'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432')
}


def conectar_db():
    """Conecta a la base de datos PostgreSQL"""
    try:
        import psycopg2
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except ImportError:
        print("❌ ERROR: psycopg2-binary no está instalado.")
        print("Instala con: pip install psycopg2-binary")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR al conectar a la base de datos: {e}")
        print(f"\nConfiguración usada:")
        print(f"  Database: {DB_CONFIG['dbname']}")
        print(f"  User: {DB_CONFIG['user']}")
        print(f"  Host: {DB_CONFIG['host']}")
        print(f"  Port: {DB_CONFIG['port']}")
        sys.exit(1)


def listar_tablas(filtro=None):
    """Lista todas las tablas de la base de datos"""
    conn = conectar_db()
    cursor = conn.cursor()

    print("\n" + "=" * 100)
    print("📊 TABLAS EN LA BASE DE DATOS: {}".format(DB_CONFIG['dbname']))
    print("=" * 100 + "\n")

    # Consulta para obtener todas las tablas
    query = """
        SELECT
            schemaname,
            tablename,
            tableowner
        FROM pg_catalog.pg_tables
        WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
    """

    if filtro:
        query += f" AND tablename LIKE '%{filtro}%'"

    query += " ORDER BY tablename;"

    cursor.execute(query)
    tablas = cursor.fetchall()

    if not tablas:
        print(f"⚠ No se encontraron tablas{' con filtro: ' + filtro if filtro else ''}")
        conn.close()
        return

    print(f"{'Nº':<5} {'Tabla':<60} {'Schema':<15} {'Owner':<20}")
    print("-" * 100)

    for idx, (schema, tabla, owner) in enumerate(tablas, 1):
        print(f"{idx:<5} {tabla:<60} {schema:<15} {owner:<20}")

    # Contar total
    print("\n" + "=" * 100)
    print(f"✓ Total de tablas: {len(tablas)}")
    print("=" * 100 + "\n")

    conn.close()


def inspeccionar_tabla(nombre_tabla):
    """Inspecciona los detalles de una tabla específica"""
    conn = conectar_db()
    cursor = conn.cursor()

    print("\n" + "=" * 100)
    print(f"🔍 INSPECCIÓN DE TABLA: {nombre_tabla}")
    print("=" * 100 + "\n")

    # Verificar si la tabla existe
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = %s
        );
    """, (nombre_tabla,))

    existe = cursor.fetchone()[0]

    if not existe:
        print(f"❌ La tabla '{nombre_tabla}' no existe.")
        print("\nTablas disponibles:")
        cursor.execute("""
            SELECT tablename
            FROM pg_catalog.pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename;
        """)
        for (tabla,) in cursor.fetchall():
            print(f"  - {tabla}")
        conn.close()
        return

    # Obtener información de columnas
    cursor.execute("""
        SELECT
            column_name,
            data_type,
            character_maximum_length,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = %s
        ORDER BY ordinal_position;
    """, (nombre_tabla,))

    columnas = cursor.fetchall()

    print(f"{'Columna':<35} {'Tipo':<25} {'Null':<6} {'Default':<30}")
    print("-" * 100)

    for col_name, data_type, max_length, is_null, default in columnas:
        tipo = data_type
        if max_length:
            tipo = f"{data_type}({max_length})"

        null_str = "Sí" if is_null == "YES" else "No"
        default_str = str(default)[:28] if default else "-"

        print(f"{col_name:<35} {tipo:<25} {null_str:<6} {default_str:<30}")

    # Obtener claves primarias
    cursor.execute("""
        SELECT a.attname
        FROM pg_index i
        JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
        WHERE i.indrelid = %s::regclass
        AND i.indisprimary;
    """, (nombre_tabla,))

    pks = cursor.fetchall()
    if pks:
        print("\n" + "-" * 100)
        print("🔑 Clave Primaria:")
        for (pk,) in pks:
            print(f"  • {pk}")

    # Obtener claves foráneas
    cursor.execute("""
        SELECT
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.table_name = %s;
    """, (nombre_tabla,))

    fks = cursor.fetchall()
    if fks:
        print("\n" + "-" * 100)
        print("🔗 Claves Foráneas:")
        for col, tabla_ref, col_ref in fks:
            print(f"  • {col} → {tabla_ref}.{col_ref}")

    # Obtener índices
    cursor.execute("""
        SELECT
            indexname,
            indexdef
        FROM pg_indexes
        WHERE schemaname = 'public'
        AND tablename = %s;
    """, (nombre_tabla,))

    indices = cursor.fetchall()
    if indices:
        print("\n" + "-" * 100)
        print("📑 Índices:")
        for idx_name, idx_def in indices:
            print(f"  • {idx_name}")

    # Contar registros
    try:
        cursor.execute(f'SELECT COUNT(*) FROM "{nombre_tabla}";')
        count = cursor.fetchone()[0]
        print("\n" + "=" * 100)
        print(f"✓ Total de registros: {count:,}")
    except Exception as e:
        print(f"\n⚠ No se pudo contar registros: {e}")

    # Mostrar primeros 5 registros
    try:
        cursor.execute(f'SELECT * FROM "{nombre_tabla}" LIMIT 5;')
        registros = cursor.fetchall()

        if registros:
            print("\n" + "-" * 100)
            print("📄 Primeros 5 registros (muestra):")
            print("-" * 100)

            # Obtener nombres de columnas
            col_names = [desc[0] for desc in cursor.description]

            for registro in registros:
                print("\nRegistro:")
                for col_name, valor in zip(col_names, registro):
                    valor_str = str(valor)[:50]
                    print(f"  {col_name:<30}: {valor_str}")
    except Exception as e:
        print(f"\n⚠ No se pudieron mostrar registros: {e}")

    print("=" * 100 + "\n")
    conn.close()


def mostrar_estadisticas():
    """Muestra estadísticas generales de la base de datos"""
    conn = conectar_db()
    cursor = conn.cursor()

    print("\n" + "=" * 100)
    print("📈 ESTADÍSTICAS DE LA BASE DE DATOS")
    print("=" * 100 + "\n")

    # Tamaño de la base de datos
    cursor.execute("""
        SELECT pg_size_pretty(pg_database_size(%s));
    """, (DB_CONFIG['dbname'],))
    size = cursor.fetchone()[0]
    print(f"💾 Tamaño total de la BD: {size}")

    # Número de tablas
    cursor.execute("""
        SELECT COUNT(*)
        FROM pg_catalog.pg_tables
        WHERE schemaname = 'public';
    """)
    num_tablas = cursor.fetchone()[0]
    print(f"📊 Número de tablas: {num_tablas}")

    # Tablas más grandes
    print("\n📦 Top 10 tablas más grandes:")
    print("-" * 100)
    cursor.execute("""
        SELECT
            schemaname || '.' || tablename AS tabla,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS tamaño,
            pg_total_relation_size(schemaname||'.'||tablename) AS bytes
        FROM pg_catalog.pg_tables
        WHERE schemaname = 'public'
        ORDER BY bytes DESC
        LIMIT 10;
    """)

    for tabla, tamaño, _ in cursor.fetchall():
        print(f"  {tabla:<50} {tamaño:>15}")

    print("=" * 100 + "\n")
    conn.close()


def main():
    """Función principal"""
    if len(sys.argv) == 1:
        # Sin argumentos: listar todas las tablas
        listar_tablas()
        mostrar_estadisticas()

    elif len(sys.argv) == 2:
        arg = sys.argv[1]

        if arg == '--help' or arg == '-h':
            print(__doc__)
            return

        elif arg == '--stats':
            mostrar_estadisticas()

        else:
            # Filtrar tablas por nombre
            listar_tablas(filtro=arg)

    elif len(sys.argv) == 3 and sys.argv[1] == '--tabla':
        # Inspeccionar tabla específica
        inspeccionar_tabla(sys.argv[2])

    else:
        print("❌ Uso incorrecto. Usa --help para ver las opciones.")
        print(__doc__)


if __name__ == '__main__':
    main()
