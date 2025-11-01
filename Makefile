# Makefile for Bankwesen Backend Services

.PHONY: help setup build up down logs clean test

help:
	@echo "Bankwesen Backend - Available Commands:"
	@echo ""
	@echo "  make setup       - Setup virtual environments for all services"
	@echo "  make build       - Build all Docker containers"
	@echo "  make up          - Start all services with Docker Compose"
	@echo "  make down        - Stop all services"
	@echo "  make logs        - View logs from all services"
	@echo "  make clean       - Clean up Docker containers and volumes"
	@echo "  make test        - Run tests (placeholder)"
	@echo ""

setup:
	@echo "Setting up all services..."
	@powershell -ExecutionPolicy Bypass -File setup.ps1

build:
	@echo "Building Docker containers..."
	docker-compose build

up:
	@echo "Starting all services..."
	docker-compose up -d
	@echo ""
	@echo "Services are starting up!"
	@echo "Gateway: http://localhost:8000/docs"
	@echo "Auth Service: http://localhost:8001/docs"
	@echo "OTP Service: http://localhost:8002/docs"
	@echo "Payment Service: http://localhost:8003/docs"
	@echo "Notification Service: http://localhost:8004/docs"
	@echo "Tuition Service: http://localhost:8005/docs"

down:
	@echo "Stopping all services..."
	docker-compose down

logs:
	docker-compose logs -f

clean:
	@echo "Cleaning up Docker resources..."
	docker-compose down -v
	docker system prune -f

test:
	@echo "Running tests..."
	@echo "Tests not yet implemented"

dev-gateway:
	@echo "Starting Gateway in development mode..."
	cd gateway && .\.venv\Scripts\Activate.ps1 && uvicorn app.main:app --reload --port 8000

dev-auth:
	@echo "Starting Auth Service in development mode..."
	cd services/auth_service && .\.venv\Scripts\Activate.ps1 && uvicorn app.main:app --reload --port 8001

dev-otp:
	@echo "Starting OTP Service in development mode..."
	cd services/otp_service && .\.venv\Scripts\Activate.ps1 && uvicorn app.main:app --reload --port 8002

dev-payment:
	@echo "Starting Payment Service in development mode..."
	cd services/payment_service && .\.venv\Scripts\Activate.ps1 && uvicorn app.main:app --reload --port 8003

dev-notification:
	@echo "Starting Notification Service in development mode..."
	cd services/notification_service && .\.venv\Scripts\Activate.ps1 && uvicorn app.main:app --reload --port 8004

dev-tuition:
	@echo "Starting Tuition Service in development mode..."
	cd services/tuition_service && .\.venv\Scripts\Activate.ps1 && uvicorn app.main:app --reload --port 8005
