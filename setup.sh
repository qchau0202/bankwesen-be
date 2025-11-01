#!/bin/bash
# Setup script for all services (Linux/Mac)

echo "Setting up Bankwesen Backend Services..."

# Array of service paths
services=(
    "gateway"
    "services/auth_service"
    "services/otp_service"
    "services/payment_service"
    "services/notification_service"
    "services/tuition_service"
)

for service in "${services[@]}"; do
    echo ""
    echo "Setting up $service..."
    
    cd "$service" || exit
    
    # Create virtual environment
    if [ -d ".venv" ]; then
        echo "  Virtual environment already exists"
    else
        echo "  Creating virtual environment..."
        python3 -m venv .venv
    fi
    
    # Activate and install dependencies
    echo "  Installing dependencies..."
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    deactivate
    
    cd - > /dev/null || exit
    
    echo "  $service setup complete!"
done

echo ""
echo "========================================"
echo "All services are set up!"
echo "========================================"
echo ""
echo "To run all services with Docker:"
echo "  docker-compose up --build"
echo ""
echo "To run a single service locally:"
echo "  cd gateway"
echo "  source .venv/bin/activate"
echo "  uvicorn app.main:app --reload --port 8000"
echo ""