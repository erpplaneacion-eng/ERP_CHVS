#!/bin/bash

echo "=========================================="
echo "EJECUTANDO TESTS - PASO 1"
echo "Sincronización de Gramajes"
echo "=========================================="
echo ""

# Activar virtualenv si existe
if [ -d "../.venv" ]; then
    echo "Activando virtualenv..."
    source ../.venv/bin/activate
elif [ -d ".venv" ]; then
    echo "Activando virtualenv..."
    source .venv/bin/activate
fi

# Ejecutar tests
echo "Ejecutando tests con Django..."
python manage.py test nutricion.tests_sincronizacion_pesos --verbosity=2

# Capturar código de salida
EXIT_CODE=$?

echo ""
echo "=========================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ TODOS LOS TESTS PASARON"
else
    echo "❌ ALGUNOS TESTS FALLARON"
fi
echo "=========================================="

exit $EXIT_CODE
