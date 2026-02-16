import os
import django
from django.db import connection
from django.apps import apps

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_chvs.settings')
django.setup()

def get_db_tables():
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
        """)
        return [row[0] for row in cursor.fetchall()]

def get_db_columns(table_name):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = %s
        """, [table_name])
        return {row[0]: {'type': row[1], 'nullable': row[2]} for row in cursor.fetchall()}

def main():
    print("="*80)
    print("DETAILED DATABASE VS MODELS COMPARISON")
    print("="*80)

    project_apps = ['principal', 'dashboard', 'nutricion', 'planeacion', 'facturacion', 'Api']
    db_tables = get_db_tables()
    
    summary = {
        'total_models': 0,
        'missing_tables': [],
        'mismatched_columns': [],
        'ok': 0
    }

    for app_label in project_apps:
        try:
            app_config = apps.get_app_config(app_label)
        except LookupError:
            print(f"Skipping app {app_label} (not found)")
            continue

        print(f"\nApp: {app_label}")
        for model in app_config.get_models():
            summary['total_models'] += 1
            table_name = model._meta.db_table
            print(f"  - Model: {model.__name__} (Table: {table_name})")
            
            if table_name not in db_tables:
                print(f"    ❌ Table NOT found in database!")
                summary['missing_tables'].append(f"{app_label}.{model.__name__} ({table_name})")
                continue

            # Compare columns
            db_columns = get_db_columns(table_name)
            model_fields = model._meta.fields
            
            mismatches = []
            for field in model_fields:
                db_column = field.column
                if db_column not in db_columns:
                    mismatches.append(f"Missing column: {db_column}")
            
            if mismatches:
                print(f"    ⚠️  Column mismatches found:")
                for m in mismatches:
                    print(f"      - {m}")
                summary['mismatched_columns'].append(f"{app_label}.{model.__name__}")
            else:
                print(f"    ✅ OK")
                summary['ok'] += 1

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total Models checked: {summary['total_models']}")
    print(f"Tables OK:           {summary['ok']}")
    print(f"Missing Tables:      {len(summary['missing_tables'])}")
    print(f"Column Mismatches:   {len(summary['mismatched_columns'])}")

    if summary['missing_tables']:
        print("\nMissing Tables Details:")
        for t in summary['missing_tables']:
            print(f"  - {t}")

    if summary['mismatched_columns']:
        print("\nMismatched Columns Details:")
        for m in summary['mismatched_columns']:
            print(f"  - {m}")

if __name__ == "__main__":
    main()
