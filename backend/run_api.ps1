# Script para ejecutar SafeMarket Backend API (Windows)
# Uso: .\run_api.ps1 -Environment "desarrollo"

param(
    [string]$Environment = "desarrollo",
    [int]$Port = 8000
)

# Función para imprimir con color
function Write-Info {
    Write-Host "ℹ️  $args" -ForegroundColor Cyan
}

function Write-Success {
    Write-Host "✅ $args" -ForegroundColor Green
}

function Write-Warning {
    Write-Host "⚠️  $args" -ForegroundColor Yellow
}

function Write-Error {
    Write-Host "❌ $args" -ForegroundColor Red
}

Clear-Host
Write-Host ""
Write-Host "╔════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║     SafeMarket Backend API - FastAPI   ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

# Verificar si existe el venv
if (-not (Test-Path "env") -and -not (Test-Path "venv")) {
    Write-Warning "Entorno virtual no encontrado"
    Write-Info "Creando entorno virtual..."
    
    try {
        python -m venv env
        Write-Success "Entorno virtual creado"
        $VENV_DIR = "env"
    }
    catch {
        Write-Error "Error al crear el entorno virtual"
        exit 1
    }
}
else {
    $VENV_DIR = if (Test-Path "env") { "env" } else { "venv" }
}

# Activar venv
Write-Info "Activando entorno virtual ($VENV_DIR)..."
try {
    & "$VENV_DIR\Scripts\Activate.ps1"
    Write-Success "Entorno virtual activado"
}
catch {
    Write-Error "No se pudo activar el entorno virtual"
    exit 1
}

# Instalar dependencias si faltan
Write-Info "Verificando dependencias..."
try {
    python -c "import fastapi" 2>$null
    Write-Success "Dependencias verificadas"
}
catch {
    Write-Warning "Instalando dependencias..."
    pip install -q -r requirements.txt
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Dependencias instaladas"
    }
    else {
        Write-Error "Error instalando dependencias"
        exit 1
    }
}

Write-Host ""
Write-Info "Iniciando SafeMarket API en modo $Environment"
Write-Info "Puerto: $Port"
Write-Host ""

# Ejecutar con configuración según ambiente
switch ($Environment.ToLower()) {
    { $_ -in "desarrollo", "dev", "development" } {
        Write-Info "🔧 Modo desarrollo (con recarga automática)"
        Write-Info "📄 Swagger UI: http://localhost:$Port/docs"
        Write-Info "📄 ReDoc: http://localhost:$Port/redoc"
        Write-Host ""
        uvicorn main:app --reload --host 0.0.0.0 --port $Port
    }
    
    { $_ -in "produccion", "prod", "production" } {
        Write-Warning "🔒 Modo producción"
        Write-Info "Usando 4 workers..."
        Write-Host ""
        
        # Verificar si gunicorn está instalado
        try {
            python -c "import gunicorn" 2>$null
        }
        catch {
            Write-Warning "gunicorn no está instalado, usando uvicorn con múltiples workers"
            uvicorn main:app --workers 4 --host 0.0.0.0 --port $Port
            exit
        }
        
        gunicorn main:app `
            --workers 4 `
            --worker-class uvicorn.workers.UvicornWorker `
            --bind "0.0.0.0:$Port"
    }
    
    default {
        Write-Error "Ambiente no reconocido: $Environment"
        Write-Info "Uso: .\run_api.ps1 -Environment 'desarrollo' -Port 8000"
        exit 1
    }
}
