#!/usr/bin/env python3
"""
Script para ver todos los registros de nutricion_requerimientos_semanales
"""

import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'erp_chvs'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'chvs2025'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432')
}

def ver_todos_registros():
    """Ver todos los registros de nutricion_requerimientos_semanales"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        print("\n" + "=" * 140)
        print("📊 TABLA: nutricion_requerimientos_semanales - TODOS LOS REGISTROS")
        print("=" * 140 + "\n")

        # Consulta con joins para mostrar nombres en lugar de IDs
        query = """
            SELECT
                r.id,
                r.modalidad_id,
                m.modalidad as modalidad_desc,
                r.componente_id,
                c.componente as componente_desc,
                r.frecuencia
            FROM nutricion_requerimientos_semanales r
            LEFT JOIN modalidades_de_consumo m ON r.modalidad_id = m.id_modalidades
            LEFT JOIN nutricion_componentes_alimentos c ON r.componente_id = c.id_componente
            ORDER BY r.modalidad_id, r.componente_id;
        """

        cursor.execute(query)
        registros = cursor.fetchall()

        if not registros:
            print("⚠ No se encontraron registros.")
            return

        # Encabezados
        print(f"{'ID':<6} {'Mod ID':<8} {'Modalidad':<45} {'Comp ID':<10} {'Componente':<35} {'Frecuencia':<20}")
        print("-" * 140)

        # Datos
        for reg in registros:
            modalidad_desc = (reg[2] or 'N/A')[:44]
            componente_desc = (reg[4] or 'N/A')[:34]
            frecuencia_texto = f"{reg[5]} veces/semana"

            print(f"{reg[0]:<6} {reg[1]:<8} {modalidad_desc:<45} {reg[3]:<10} {componente_desc:<35} {frecuencia_texto:<20}")

        print("\n" + "=" * 140)
        print(f"✓ Total de registros: {len(registros)}")
        print("=" * 140 + "\n")

        # Resumen por modalidad
        print("\n📈 RESUMEN POR MODALIDAD:")
        print("-" * 100)

        cursor.execute("""
            SELECT
                r.modalidad_id,
                m.modalidad,
                COUNT(*) as total_componentes
            FROM nutricion_requerimientos_semanales r
            LEFT JOIN modalidades_de_consumo m ON r.modalidad_id = m.id_modalidades
            GROUP BY r.modalidad_id, m.modalidad
            ORDER BY r.modalidad_id;
        """)

        resumen = cursor.fetchall()
        print(f"\n{'Modalidad ID':<15} {'Descripción':<60} {'Total Componentes':<20}")
        print("-" * 100)
        for mod_id, mod_desc, total in resumen:
            descripcion = (mod_desc or 'N/A')[:59]
            print(f"{mod_id:<15} {descripcion:<60} {total:<20}")

        print("\n" + "-" * 100)

        # Detalle por modalidad
        print("\n\n📋 DETALLE POR MODALIDAD:")
        print("=" * 140 + "\n")

        for mod_id, mod_desc, _ in resumen:
            print(f"\n🔹 MODALIDAD: {mod_id} - {mod_desc}")
            print("-" * 140)

            cursor.execute("""
                SELECT
                    c.componente,
                    r.frecuencia
                FROM nutricion_requerimientos_semanales r
                LEFT JOIN nutricion_componentes_alimentos c ON r.componente_id = c.id_componente
                WHERE r.modalidad_id = %s
                ORDER BY r.componente_id;
            """, (mod_id,))

            componentes = cursor.fetchall()
            for comp_desc, frecuencia in componentes:
                print(f"  • {comp_desc:<50} → {frecuencia} veces por semana")

        print("\n" + "=" * 140 + "\n")

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    ver_todos_registros()
