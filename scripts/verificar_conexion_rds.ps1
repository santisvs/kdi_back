# Script para verificar la conexion a RDS desde Elastic Beanstalk
# Este script te ayuda a diagnosticar problemas de conectividad

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Verificar Conexion RDS desde EB" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que AWS CLI este instalado
try {
    $awsVersion = aws --version 2>&1
    Write-Host "[OK] AWS CLI instalado: $awsVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] AWS CLI no esta instalado" -ForegroundColor Red
    Write-Host "  Instala con: pip install awscli" -ForegroundColor Yellow
    exit 1
}

# Solicitar informacion
Write-Host "Necesito algunos datos para verificar la configuracion:" -ForegroundColor Yellow
Write-Host ""

$envName = Read-Host "Nombre del entorno de Elastic Beanstalk (ej: kdi-back-prod)"
$rdsInstanceId = Read-Host "ID o nombre de la instancia RDS (ej: kdi-back-db)"

Write-Host ""
Write-Host "Obteniendo informacion..." -ForegroundColor Cyan
Write-Host ""

# Variables para el resumen
$missingVars = @()
$hasCorrectRule = $false
$ebSGId = $null

# Obtener Security Group de Elastic Beanstalk
Write-Host "1. Obteniendo Security Group de Elastic Beanstalk..." -ForegroundColor Cyan
try {
    $ebEnv = aws elasticbeanstalk describe-environments --environment-names $envName --query 'Environments[0]' --output json | ConvertFrom-Json
    
    if (-not $ebEnv) {
        Write-Host "[ERROR] No se encontro el entorno: $envName" -ForegroundColor Red
        exit 1
    }
    
    $ebEnvId = $ebEnv.EnvironmentId
    Write-Host "  Environment ID: $ebEnvId" -ForegroundColor Gray
    
    # Obtener instancias EC2 del entorno
    $ebInstances = aws ec2 describe-instances `
        --filters "Name=tag:elasticbeanstalk:environment-id,Values=$ebEnvId" `
        --query 'Reservations[*].Instances[*].[InstanceId,SecurityGroups[0].GroupId,SecurityGroups[0].GroupName]' `
        --output json | ConvertFrom-Json
    
    if ($ebInstances -and $ebInstances.Count -gt 0) {
        $ebSGId = $ebInstances[0][1]
        $ebSGName = $ebInstances[0][2]
        Write-Host "  [OK] Security Group de EB: $ebSGId ($ebSGName)" -ForegroundColor Green
    } else {
        Write-Host "  [ADVERTENCIA] No se encontraron instancias EC2 del entorno" -ForegroundColor Yellow
        Write-Host "    Puedes encontrarlo manualmente en:" -ForegroundColor Yellow
        Write-Host "    EB Console -> Configuration -> Instances -> EC2 security groups" -ForegroundColor Yellow
        $ebSGId = Read-Host "    Ingresa el Security Group ID de EB manualmente"
    }
} catch {
    Write-Host "  [ERROR] Error al obtener informacion de EB: $_" -ForegroundColor Red
    Write-Host "    Asegurate de tener las credenciales de AWS configuradas" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Obtener Security Group de RDS
Write-Host "2. Obteniendo Security Group de RDS..." -ForegroundColor Cyan
$rdsSGId = $null
try {
    $rdsInstance = aws rds describe-db-instances --db-instance-identifier $rdsInstanceId --query 'DBInstances[0]' --output json | ConvertFrom-Json
    
    if (-not $rdsInstance) {
        Write-Host "[ERROR] No se encontro la instancia RDS: $rdsInstanceId" -ForegroundColor Red
        exit 1
    }
    
    $rdsEndpoint = $rdsInstance.Endpoint.Address
    $rdsPort = $rdsInstance.Endpoint.Port
    $rdsVPC = $rdsInstance.DBSubnetGroup.VpcId
    $rdsSGId = $rdsInstance.VpcSecurityGroups[0].VpcSecurityGroupId
    
    Write-Host "  [OK] Endpoint de RDS: $rdsEndpoint" -ForegroundColor Green
    Write-Host "  [OK] Puerto: $rdsPort" -ForegroundColor Green
    Write-Host "  [OK] VPC: $rdsVPC" -ForegroundColor Green
    Write-Host "  [OK] Security Group de RDS: $rdsSGId" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Error al obtener informacion de RDS: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Verificar reglas del Security Group de RDS
Write-Host "3. Verificando reglas del Security Group de RDS..." -ForegroundColor Cyan
try {
    $rdsSGRules = aws ec2 describe-security-groups `
        --group-ids $rdsSGId `
        --query 'SecurityGroups[0].IpPermissions[?ToPort==`5432`]' `
        --output json | ConvertFrom-Json
    
    $hasCorrectRule = $false
    if ($rdsSGRules -and $rdsSGRules.Count -gt 0) {
        foreach ($rule in $rdsSGRules) {
            if ($rule.UserIdGroupPairs) {
                foreach ($pair in $rule.UserIdGroupPairs) {
                    if ($pair.GroupId -eq $ebSGId) {
                        Write-Host "  [OK] Regla encontrada: PostgreSQL (5432) desde $ebSGId" -ForegroundColor Green
                        $hasCorrectRule = $true
                        break
                    }
                }
            }
            if ($rule.IpRanges) {
                foreach ($range in $rule.IpRanges) {
                    $cidrIp = $range.CidrIp
                    Write-Host "  [ADVERTENCIA] Regla encontrada: PostgreSQL (5432) desde $cidrIp" -ForegroundColor Yellow
                    if ($cidrIp -eq "0.0.0.0/0") {
                        Write-Host "    [ADVERTENCIA] Esto permite acceso desde cualquier lugar" -ForegroundColor Red
                    }
                }
            }
        }
    }
    
    if (-not $hasCorrectRule) {
        Write-Host "  [ERROR] NO se encontro una regla que permita conexiones desde el Security Group de EB" -ForegroundColor Red
        Write-Host ""
        Write-Host "  SOLUCION:" -ForegroundColor Yellow
        Write-Host "  1. Ve a EC2 -> Security Groups -> $rdsSGId" -ForegroundColor Yellow
        Write-Host "  2. Inbound rules -> Edit inbound rules -> Add rule" -ForegroundColor Yellow
        Write-Host "  3. Type: PostgreSQL (5432)" -ForegroundColor Yellow
        Write-Host "  4. Source: $ebSGId (Security Group de EB)" -ForegroundColor Yellow
        Write-Host "  5. Save rules" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  [ERROR] Error al verificar reglas: $_" -ForegroundColor Red
}

Write-Host ""

# Verificar variables de entorno
Write-Host "4. Verificando variables de entorno en Elastic Beanstalk..." -ForegroundColor Cyan
try {
    $ebEnvVars = aws elasticbeanstalk describe-configuration-settings `
        --application-name $ebEnv.ApplicationName `
        --environment-name $envName `
        --query 'ConfigurationSettings[0].OptionSettings[?Namespace==`aws:elasticbeanstalk:application:environment`]' `
        --output json | ConvertFrom-Json
    
    $requiredVars = @("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD")
    $missingVars = @()
    
    foreach ($var in $requiredVars) {
        $found = $false
        foreach ($envVar in $ebEnvVars) {
            if ($envVar.OptionName -eq $var) {
                if ($var -eq "DB_PASSWORD") {
                    Write-Host "  [OK] ${var}: ********" -ForegroundColor Green
                } else {
                    $varValue = $envVar.Value
                    Write-Host "  [OK] ${var} = $varValue" -ForegroundColor Green
                }
                $found = $true
                break
            }
        }
        if (-not $found) {
            Write-Host "  [ERROR] ${var}: NO CONFIGURADA" -ForegroundColor Red
            $missingVars += $var
        }
    }
    
    if ($missingVars.Count -gt 0) {
        Write-Host ""
        Write-Host "  SOLUCION: Configura las variables de entorno faltantes" -ForegroundColor Yellow
        Write-Host "  eb setenv DB_HOST=... DB_PORT=5432 DB_NAME=... DB_USER=... DB_PASSWORD=..." -ForegroundColor Yellow
    }
} catch {
    Write-Host "  [ERROR] Error al verificar variables de entorno: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Resumen" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Para que la conexion funcione, necesitas:" -ForegroundColor Yellow

$varsOk = $missingVars.Count -eq 0
$varsColor = if ($varsOk) { "Green" } else { "Red" }
Write-Host "  1. Variables de entorno DB_* configuradas en EB" -ForegroundColor $varsColor

$sgOk = $hasCorrectRule
$sgColor = if ($sgOk) { "Green" } else { "Red" }
Write-Host "  2. Security Group de RDS permite conexiones desde $ebSGId" -ForegroundColor $sgColor

Write-Host "  3. RDS esta disponible y accesible" -ForegroundColor "Green"
Write-Host ""
Write-Host "Si todo esta configurado correctamente, el problema puede ser:" -ForegroundColor Yellow
Write-Host "  - Las instancias de EB aun no se han reiniciado despues de configurar las variables" -ForegroundColor Yellow
Write-Host "  - Timeout de conexion (verifica que RDS este en la misma region o VPC)" -ForegroundColor Yellow
Write-Host "  - PostGIS no esta instalado en RDS" -ForegroundColor Yellow
Write-Host ""
