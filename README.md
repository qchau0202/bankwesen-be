# Bankwesen Backend - Microservices Architecture

This repository contains a simple FastAPI-based microservices stack designed to demonstrate inter-service communication behind an API gateway. Each service exposes a hello world endpoint, a health check, and a downstream call to another service. MongoDB is included for completeness, although the sample handlers do not persist data.

## Architecture Overview
- Gateway (`8000`): entry point and service fan-out
- Auth Service (`8001`): calls OTP Service
- OTP Service (`8002`): calls Notification Service
- Payment Service (`8003`): calls Auth Service
- Notification Service (`8004`): calls Tuition Service
- Tuition Service (`8005`): calls Payment Service
- MongoDB (`27017`): shared database instance (one database per service)

All services are packaged with Dockerfiles and orchestrated with `docker-compose`.
## Prerequisites
- Docker Desktop (or Docker Engine with the Docker Compose plugin)
- Optional: Python 3.11 or newer if you plan to run services directly on your machine

## Quick Start with Docker Compose

1. Clone the repository and move into the project directory:
   ```bash
   git clone <repo-url>
   cd bankwesen-be
   ```
2. Build and start the entire stack:
   ```bash
   docker-compose up --build
   ```
3. Wait for the services to report that they are running. FastAPI will log the available URLs as each service boots.
4. Verify the deployment:
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8000/call-all
   ```
   The second command should return a JSON payload containing responses from every downstream service.
5. Stop the stack when you are done:
   ```bash
   docker-compose down
   # Add -v if you want to remove the MongoDB volume
   # docker-compose down -v
   ```

### Service Documentation

Each FastAPI service exposes interactive OpenAPI documentation at `/docs` on its respective port. For example, the gateway docs are available at `http://localhost:8000/docs` once the containers are running.

## Local Development Without Docker
If you prefer to run the services locally, set up a virtual environment for each one.

### Windows (PowerShell)

```powershell
./setup.ps1
```

This script creates `.venv` directories, installs dependencies, and prepares each service for local development. Launch a service by activating its environment and running Uvicorn:

```powershell
cd gateway
./.venv/Scripts/Activate.ps1
uvicorn app.main:app --reload --port 8000
```

### macOS / Linux (Bash)
```bash
./setup.sh
```

After setup, activate a service environment and start Uvicorn:
```bash
cd gateway
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Repeat the same steps inside any service directory under `services/` to run it locally.

## Testing the APIs
- Gateway hello world: `curl http://localhost:8000/hello`
- Individual hello endpoints: `curl http://localhost:8001/hello` through `curl http://localhost:8005/hello`
- Inter-service call chain:
  - `curl http://localhost:8000/call-all`
  - `curl http://localhost:8001/call-otp`
  - `curl http://localhost:8002/call-notification`
  - `curl http://localhost:8003/call-auth`
  - `curl http://localhost:8004/call-tuition`
  - `curl http://localhost:8005/call-payment`

## Environment Variables

The Docker Compose file provides default values for service-to-service URLs and MongoDB connections. Override them as needed via environment variables or `.env` files:

- `AUTH_SERVICE_URL`, `OTP_SERVICE_URL`, `PAYMENT_SERVICE_URL`, `NOTIFICATION_SERVICE_URL`, `TUITION_SERVICE_URL`: downstream service endpoints
- `MONGODB_URL`: MongoDB connection string (each service uses its own database when running in Docker)

## Project Structure

```
bankwesen-be/
├── docker-compose.yml
├── Makefile
├── setup.ps1
├── setup.sh
├── gateway/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/main.py
└── services/
    ├── auth_service/
    ├── otp_service/
    ├── payment_service/
    ├── notification_service/
    └── tuition_service/
```

Each service directory mirrors the gateway layout with its own `Dockerfile`, `requirements.txt`, and FastAPI application module.

## Troubleshooting

- **Port conflicts**: Stop the conflicting process or adjust host port mappings in `docker-compose.yml`.
- **Service not responding**: Inspect logs with `docker-compose logs -f <service>` and confirm dependencies are healthy.
- **Reset MongoDB data**: Remove the persistent volume by running `docker-compose down -v` before the next `docker-compose up`.