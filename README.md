# Bankwesen Backend - Microservices Architecture

This repository contains a simple FastAPI-based microservices stack designed to demonstrate inter-service communication behind an API gateway. Each service exposes a hello world endpoint, a health check, and a downstream call to another service. MongoDB is included for completeness, although the sample handlers do not persist data.

## Architecture Overview
- Gateway (`8000`): entry point and service fan-out
- Auth Service (`8001`): calls OTP Service
- OTP Service (`8002`): OTP generation and verification with Redis, calls Notification Service
- Payment Service (`8003`): calls Auth Service
- Notification Service (`8004`): email notifications via SMTP, calls Tuition Service
- Tuition Service (`8005`): calls Payment Service
- MongoDB (`27017`): shared database instance (one database per service)
- Redis (`6379`): OTP storage and session management

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

## Database Configuration

This project uses **separate MongoDB databases** for each service following microservices best practices:

- **auth_db**: User authentication and management (Auth Service)
- **tuition_db**: Student records and tuition fees (Tuition Service)
- **payment_db**: Payment processing and transactions (Payment Service)

### Initialize Databases

Initialize all databases with sample data:
```powershell
python init_all_databases.py
```

Or initialize individually:
```powershell
# Auth database
cd services/auth_service
python insert_test_users.py

# Tuition database
cd ../tuition_service
python init_tuition_db.py

# Payment database
cd ../payment_service
python init_payment_db.py
```

📚 **See detailed database documentation**: [DATABASE_SETUP.md](DATABASE_SETUP.md)  
📋 **Configuration summary**: [CONFIGURATION_SUMMARY.md](CONFIGURATION_SUMMARY.md)

## Environment Variables

Each service requires its own `.env` file with the following variables:

- `MONGODB_URL`: MongoDB connection string (MongoDB Atlas cloud database)
- `DATABASE_NAME`: Service-specific database name (auth_db, tuition_db, or payment_db)
- `API_KEY`: API key for service-to-service authentication
- `JWT_SECRET_KEY`: Secret key for JWT token generation
- Service URLs: `AUTH_SERVICE_URL`, `OTP_SERVICE_URL`, `PAYMENT_SERVICE_URL`, `NOTIFICATION_SERVICE_URL`, `TUITION_SERVICE_URL`

### OTP Service Specific:
- `REDIS_URL`: Redis connection string (e.g., redis://redis:6379)
- `OTP_LENGTH`: Length of OTP code (default: 6)
- `OTP_EXPIRATION`: OTP expiration time in seconds (default: 60)
- `OTP_MAX_ATTEMPTS`: Maximum verification attempts (default: 3)

### Notification Service Specific:
- `SMTP_HOST`: SMTP server host (e.g., smtp.gmail.com)
- `SMTP_PORT`: SMTP server port (default: 587)
- `SMTP_USER`: SMTP username/email
- `SMTP_PASSWORD`: SMTP password or app password
- `SMTP_FROM_EMAIL`: Sender email address

## Project Structure

```
bankwesen-be/
├── docker-compose.yml       # Docker orchestration with MongoDB + Redis
├── Makefile                 # Build and deployment commands
├── setup.ps1                # Windows setup script
├── setup.sh                 # Mac/Linux setup script
├── init_all_databases.py    # Initialize all databases with sample data
├── gateway/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/main.py
└── services/
    ├── auth_service/         # User authentication with JWT
    ├── otp_service/          # OTP generation/verification with Redis
    ├── payment_service/      # Payment processing
    ├── notification_service/ # Email notifications via SMTP
    └── tuition_service/      # Tuition fee management
```

Each service directory mirrors the gateway layout with its own `Dockerfile`, `requirements.txt`, and FastAPI application module.

## Troubleshooting

- **Port conflicts**: Stop the conflicting process or adjust host port mappings in `docker-compose.yml`.
- **Service not responding**: Inspect logs with `docker-compose logs -f <service>` and confirm dependencies are healthy.
- **Reset MongoDB data**: Remove the persistent volume by running `docker-compose down -v` before the next `docker-compose up`.