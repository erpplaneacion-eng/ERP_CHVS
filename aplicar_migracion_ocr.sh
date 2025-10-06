#!/bin/bash

echo "========================================"
echo "  Aplicando Migración OCR Validation"
echo "========================================"
echo ""

cd erp_chvs

echo "[1/2] Aplicando migración..."
python manage.py migrate ocr_validation
echo ""

echo "[2/2] Verificando migración..."
python manage.py showmigrations ocr_validation
echo ""

echo "========================================"
echo "  Migración Completada"
echo "========================================"
echo ""
