# Script para ejecutar la API SafeMarket
Set-Location "c:\Eaq\Proyectos\SafeMarket\Aplicativo\safemarket_proyecto\backend"
Write-Host "[INFO] Directorio actual: $(Get-Location)" -ForegroundColor Cyan
Write-Host "[INFO] Iniciando SafeMarket API en puerto 8000..." -ForegroundColor Green
Write-Host ""

python main.py
