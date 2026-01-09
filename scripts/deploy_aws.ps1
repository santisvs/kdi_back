# Script de despliegue rápido para AWS Elastic Beanstalk (PowerShell)
# Uso: .\scripts\deploy_aws.ps1 [environment-name]

param(
    [string]$Environment = "kdi-back-prod"
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Desplegando KDI Back a AWS" -ForegroundColor Cyan
Write-Host "Entorno: $Environment" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Verificar que EB CLI está instalado
try {
    $null = Get-Command eb -ErrorAction Stop
} catch {
    Write-Host "❌ EB CLI no está instalado. Instálalo con: pip install awsebcli" -ForegroundColor Red
    exit 1
}

# Verificar que estamos en el directorio correcto
if (-not (Test-Path "application.py")) {
    Write-Host "❌ No se encuentra application.py. Asegúrate de estar en la raíz del proyecto." -ForegroundColor Red
    exit 1
}

# Verificar que requirements.txt existe
if (-not (Test-Path "requirements.txt")) {
    Write-Host "❌ No se encuentra requirements.txt" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "📦 Verificando configuración..." -ForegroundColor Yellow
try {
    eb status $Environment | Out-Null
} catch {
    Write-Host "⚠️  El entorno no existe. Créalo primero con: eb create $Environment" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🚀 Desplegando aplicación..." -ForegroundColor Green
eb deploy $Environment

Write-Host ""
Write-Host "✅ Despliegue completado!" -ForegroundColor Green
Write-Host ""
Write-Host "Para ver los logs:" -ForegroundColor Cyan
Write-Host "  eb logs $Environment"
Write-Host ""
Write-Host "Para abrir en el navegador:" -ForegroundColor Cyan
Write-Host "  eb open $Environment"
Write-Host ""
Write-Host "Para ver el estado:" -ForegroundColor Cyan
Write-Host "  eb status $Environment"

