#!/bin/bash

# Script para ejecutar SafeMarket Backend API
# Uso: ./run_api.sh [desarrollo|producción]

ENVIRONMENT=${1:-"desarrollo"}
PORT=${PORT:-8000}

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Función para imprimir con color
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

clear
echo -e "${GREEN}"
echo "╔════════════════════════════════════════╗"
echo "║     SafeMarket Backend API - FastAPI   ║"
echo "╚════════════════════════════════════════╝"
echo -e "${NC}"

# Verificar si existe el venv
if [ ! -d "env" ] && [ ! -d "venv" ]; then
    print_warning "Entorno virtual no encontrado"
    print_info "Creando entorno virtual..."
    
    if python -m venv env; then
        print_success "Entorno virtual creado"
    else
        print_error "Error al crear el entorno virtual"
        exit 1
    fi
fi

# Detectar el venv
if [ -d "env" ]; then
    VENV_DIR="env"
else
    VENV_DIR="venv"
fi

# Activar venv
print_info "Activando entorno virtual ($VENV_DIR)..."
if [ -f "$VENV_DIR/Scripts/activate" ]; then
    # Windows
    source "$VENV_DIR/Scripts/activate"
elif [ -f "$VENV_DIR/bin/activate" ]; then
    # Unix/Linux/Mac
    source "$VENV_DIR/bin/activate"
else
    print_error "No se pudo activar el entorno virtual"
    exit 1
fi

print_success "Entorno virtual activado"

# Verificar dependencias
print_info "Verificando dependencias..."
if ! python -c "import fastapi" 2>/dev/null; then
    print_warning "Instalando dependencias..."
    pip install -q -r requirements.txt
    if [ $? -eq 0 ]; then
        print_success "Dependencias instaladas"
    else
        print_error "Error instalando dependencias"
        exit 1
    fi
else
    print_success "Dependencias verificadas"
fi

echo ""
print_info "Iniciando SafeMarket API en modo $ENVIRONMENT"
print_info "Puerto: $PORT"
echo ""

# Ejecutar con configuración según ambiente
case $ENVIRONMENT in
    "desarrollo" | "dev" | "development")
        print_info "🔧 Modo desarrollo (con recarga automática)"
        print_info "📄 Swagger UI: http://localhost:$PORT/docs"
        print_info "📄 ReDoc: http://localhost:$PORT/redoc"
        echo ""
        uvicorn main:app --reload --host 0.0.0.0 --port $PORT
        ;;
    
    "produccion" | "prod" | "production")
        print_warning "🔒 Modo producción"
        print_info "Usando 4 workers..."
        echo ""
        gunicorn main:app \
            --workers 4 \
            --worker-class uvicorn.workers.UvicornWorker \
            --bind 0.0.0.0:$PORT
        ;;
    
    *)
        print_error "Ambiente no reconocido: $ENVIRONMENT"
        print_info "Uso: ./run_api.sh [desarrollo|produccion]"
        exit 1
        ;;
esac
