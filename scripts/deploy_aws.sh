#!/bin/bash
# Script de despliegue rápido para AWS Elastic Beanstalk
# Uso: ./scripts/deploy_aws.sh [environment-name]

set -e

ENVIRONMENT=${1:-kdi-back-prod}

echo "=========================================="
echo "Desplegando KDI Back a AWS"
echo "Entorno: $ENVIRONMENT"
echo "=========================================="

# Verificar que EB CLI está instalado
if ! command -v eb &> /dev/null; then
    echo "❌ EB CLI no está instalado. Instálalo con: pip install awsebcli"
    exit 1
fi

# Verificar que estamos en el directorio correcto
if [ ! -f "application.py" ]; then
    echo "❌ No se encuentra application.py. Asegúrate de estar en la raíz del proyecto."
    exit 1
fi

# Verificar que requirements.txt existe
if [ ! -f "requirements.txt" ]; then
    echo "❌ No se encuentra requirements.txt"
    exit 1
fi

echo ""
echo "📦 Verificando configuración..."
eb status $ENVIRONMENT || echo "⚠️  El entorno no existe. Créalo primero con: eb create $ENVIRONMENT"

echo ""
echo "🚀 Desplegando aplicación..."
eb deploy $ENVIRONMENT

echo ""
echo "✅ Despliegue completado!"
echo ""
echo "Para ver los logs:"
echo "  eb logs $ENVIRONMENT"
echo ""
echo "Para abrir en el navegador:"
echo "  eb open $ENVIRONMENT"
echo ""
echo "Para ver el estado:"
echo "  eb status $ENVIRONMENT"

