#!/bin/bash

# ============================================
# Script de verificación PRE-PUSH
# ============================================
# Este script verifica que no haya credenciales
# sensibles antes de hacer push a GitHub/Railway

echo "🔍 Verificando seguridad antes del push..."
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0

# 1. Verificar que .env NO esté en git
echo "📁 Verificando que .env no esté trackeado..."
if git ls-files | grep -q "\.env$"; then
    echo -e "${RED}❌ ERROR: .env está siendo trackeado por git${NC}"
    echo "   Ejecuta: git rm --cached erp_chvs/.env"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✅ .env no está en git${NC}"
fi
echo ""

# 2. Buscar API keys en archivos staged
echo "🔑 Buscando API keys en archivos staged..."
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(py|md|txt|toml|json)$')

if [ -n "$STAGED_FILES" ]; then
    # Patrones de API keys conocidas (primeros caracteres)
    if echo "$STAGED_FILES" | xargs grep -l "AIzaSy" 2>/dev/null; then
        echo -e "${RED}❌ ERROR: Gemini API Key encontrada en archivos staged${NC}"
        ERRORS=$((ERRORS + 1))
    fi

    if echo "$STAGED_FILES" | xargs grep -l "kCMyClLzY" 2>/dev/null; then
        echo -e "${RED}❌ ERROR: Database password encontrada en archivos staged${NC}"
        ERRORS=$((ERRORS + 1))
    fi

    if echo "$STAGED_FILES" | xargs grep -l "Zjd6bWZk" 2>/dev/null; then
        echo -e "${RED}❌ ERROR: LandingAI API Key encontrada en archivos staged${NC}"
        ERRORS=$((ERRORS + 1))
    fi
fi

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ No se encontraron API keys en archivos staged${NC}"
fi
echo ""

# 3. Verificar que requirements.txt tenga gunicorn y whitenoise
echo "📦 Verificando dependencias de producción..."
if ! grep -q "gunicorn" erp_chvs/requirements.txt; then
    echo -e "${YELLOW}⚠️  ADVERTENCIA: gunicorn no está en requirements.txt${NC}"
    ERRORS=$((ERRORS + 1))
fi

if ! grep -q "whitenoise" erp_chvs/requirements.txt; then
    echo -e "${YELLOW}⚠️  ADVERTENCIA: whitenoise no está en requirements.txt${NC}"
    ERRORS=$((ERRORS + 1))
fi

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ Dependencias de producción OK${NC}"
fi
echo ""

# 4. Verificar archivos de configuración Railway
echo "🚂 Verificando archivos de configuración Railway..."
MISSING_FILES=0

if [ ! -f "runtime.txt" ]; then
    echo -e "${RED}❌ Falta: runtime.txt${NC}"
    MISSING_FILES=$((MISSING_FILES + 1))
fi

if [ ! -f "Procfile" ]; then
    echo -e "${RED}❌ Falta: Procfile${NC}"
    MISSING_FILES=$((MISSING_FILES + 1))
fi

if [ ! -f "railway.toml" ]; then
    echo -e "${YELLOW}⚠️  Opcional: railway.toml${NC}"
fi

if [ ! -f "erp_chvs/.env.example" ]; then
    echo -e "${YELLOW}⚠️  Falta: erp_chvs/.env.example${NC}"
fi

if [ $MISSING_FILES -eq 0 ]; then
    echo -e "${GREEN}✅ Archivos de configuración OK${NC}"
else
    ERRORS=$((ERRORS + MISSING_FILES))
fi
echo ""

# 5. Verificar que staticfiles/ esté en .gitignore
echo "📂 Verificando .gitignore..."
if ! grep -q "staticfiles" .gitignore; then
    echo -e "${YELLOW}⚠️  staticfiles/ no está en .gitignore${NC}"
fi

if ! grep -q "^\.env$" .gitignore; then
    echo -e "${RED}❌ ERROR: .env no está en .gitignore${NC}"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✅ .gitignore configurado correctamente${NC}"
fi
echo ""

# Resultado final
echo "============================================"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ VERIFICACIÓN EXITOSA${NC}"
    echo "   Es seguro hacer push a GitHub/Railway"
    echo ""
    echo "Comandos sugeridos:"
    echo "  git push origin master"
    exit 0
else
    echo -e "${RED}❌ VERIFICACIÓN FALLIDA: $ERRORS errores encontrados${NC}"
    echo "   NO hagas push hasta corregir los errores"
    echo ""
    echo "Para más información, consulta:"
    echo "  - DEPLOY_RAILWAY.md"
    echo "  - .env.example"
    exit 1
fi
