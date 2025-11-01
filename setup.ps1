# Setup script for all services
Write-Host "Setting up Bankwesen Backend Services..." -ForegroundColor Green

# Array of service paths
$services = @(
    "gateway",
    "services\auth_service",
    "services\otp_service",
    "services\payment_service",
    "services\notification_service",
    "services\tuition_service"
)

foreach ($service in $services) {
    Write-Host "`nSetting up $service..." -ForegroundColor Cyan
    
    Push-Location $service
    
    # Create virtual environment
    if (Test-Path ".venv") {
        Write-Host "  Virtual environment already exists" -ForegroundColor Yellow
    }
    else {
        Write-Host "  Creating virtual environment..." -ForegroundColor Gray
        python -m venv .venv
    }
    
    # Activate and install dependencies
    Write-Host "  Installing dependencies..." -ForegroundColor Gray
    .\.venv\Scripts\Activate.ps1
    pip install --upgrade pip
    pip install -r requirements.txt
    deactivate
    
    Pop-Location
    
    Write-Host "  $service setup complete!" -ForegroundColor Green
}

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "All services are set up!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "`nTo run all services with Docker:" -ForegroundColor Cyan
Write-Host "  docker-compose up --build" -ForegroundColor White
Write-Host "`nTo run a single service locally:" -ForegroundColor Cyan
Write-Host "  cd gateway" -ForegroundColor White
Write-Host "  .\.venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  uvicorn app.main:app --reload --port 8000" -ForegroundColor White
Write-Host ""