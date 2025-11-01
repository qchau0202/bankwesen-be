# Bankwesen Backend - Microservices with FastAPI & MongoDB# Bankwesen Backend - Microservices Architecture



Simple microservices architecture with hello world APIs to test inter-service communication.This is a microservices-based banking system backend built with FastAPI and Docker.



## 🏗️ Architecture## 🏗️ Architecture



- **Gateway** (Port 8000): API GatewayThe system consists of the following services:

- **Auth Service** (Port 8001): Authentication service

- **OTP Service** (Port 8002): OTP service- **Gateway** (Port 8000): API Gateway for routing requests to microservices

- **Payment Service** (Port 8003): Payment service- **Auth Service** (Port 8001): Authentication and authorization

- **Notification Service** (Port 8004): Notification service- **OTP Service** (Port 8002): One-time password generation and verification

- **Tuition Service** (Port 8005): Tuition service- **Payment Service** (Port 8003): Payment processing

- **MongoDB** (Port 27017): Database- **Notification Service** (Port 8004): Notification management

- **Tuition Service** (Port 8005): Tuition fee management

## 🚀 Quick Start

## 🚀 Quick Start

### Using Docker Compose (Recommended)

### Prerequisites

```powershell

# Start all services- Docker and Docker Compose

docker-compose up --build- Python 3.11+ (for local development)



# Stop all services### Running with Docker Compose (Recommended)

docker-compose down

```1. Clone the repository

2. Navigate to the project root

### Local Development with .venv3. Run all services:



```powershell```bash

# Setup all servicesdocker-compose up --build

.\setup.ps1```



# Run individual serviceThis will start all services, PostgreSQL database, and Redis cache.

cd gateway

.\.venv\Scripts\activate### Access the Services

uvicorn app.main:app --reload --port 8000

```- **API Gateway**: http://localhost:8000

- **Gateway Docs**: http://localhost:8000/docs

## 📡 Test Endpoints- **Auth Service**: http://localhost:8001/docs

- **OTP Service**: http://localhost:8002/docs

### Test Individual Services- **Payment Service**: http://localhost:8003/docs

- **Notification Service**: http://localhost:8004/docs

```bash- **Tuition Service**: http://localhost:8005/docs

# Gateway

curl http://localhost:8000/hello### Health Check



# Auth ServiceCheck all services health status:

curl http://localhost:8001/hello```bash

curl http://localhost:8000/health

# OTP Service```

curl http://localhost:8002/hello

## 🛠️ Local Development Setup

# Payment Service

curl http://localhost:8003/hello### Setting up Virtual Environment



# Notification ServiceFor each service, you can set up a local virtual environment:

curl http://localhost:8004/hello

```bash

# Tuition Service# Navigate to service directory

curl http://localhost:8005/hellocd gateway  # or services/auth_service, etc.

```

# Create virtual environment

### Test Inter-Service Communicationpython -m venv .venv



```bash# Activate virtual environment

# Gateway calls all services# On Windows:

curl http://localhost:8000/call-all.venv\Scripts\activate

# On Linux/Mac:

# Auth calls OTPsource .venv/bin/activate

curl http://localhost:8001/call-otp

# Install dependencies

# OTP calls Notificationpip install -r requirements.txt

curl http://localhost:8002/call-notification

# Run the service

# Payment calls Authuvicorn app.main:app --reload --port 8000

curl http://localhost:8003/call-auth```



# Notification calls Tuition## 🐳 Docker Commands

curl http://localhost:8004/call-tuition

### Build all services

# Tuition calls Payment```bash

curl http://localhost:8005/call-paymentdocker-compose build

``````



## 📚 API Documentation### Start all services

```bash

Interactive API docs available at:docker-compose up

- Gateway: http://localhost:8000/docs```

- Auth: http://localhost:8001/docs

- OTP: http://localhost:8002/docs### Start services in detached mode

- Payment: http://localhost:8003/docs```bash

- Notification: http://localhost:8004/docsdocker-compose up -d

- Tuition: http://localhost:8005/docs```



## 🗄️ Database### Stop all services

```bash

This project uses **MongoDB** (not PostgreSQL):docker-compose down

- Connection: `mongodb://localhost:27017````

- Each service has its own database

### View logs

## 📦 Technology Stack```bash

docker-compose logs -f

- **Framework**: FastAPI```

- **Server**: Uvicorn

- **Database**: MongoDB### View logs for specific service

- **Python**: 3.11+```bash

- **Container**: Docker & Docker Composedocker-compose logs -f auth_service

```

## 🐳 Docker Commands

### Rebuild and restart specific service

```bash```bash

# Build all servicesdocker-compose up --build auth_service

docker-compose build```



# Start all services### Run individual service

docker-compose up```bash

# Build individual service

# Start in backgrounddocker build -t bankwesen-auth ./services/auth_service

docker-compose up -d

# Run individual service

# View logsdocker run -p 8001:8001 bankwesen-auth

docker-compose logs -f```



# Stop all services## 📁 Project Structure

docker-compose down

```

# Clean up everythingbankwesen-be/

docker-compose down -v├── docker-compose.yml          # Docker Compose configuration

```├── README.md                   # This file

├── gateway/                    # API Gateway

## 📁 Project Structure│   ├── Dockerfile

│   ├── requirements.txt

```│   ├── README.md

bankwesen-be/│   └── app/

├── docker-compose.yml          # Docker orchestration│       └── main.py

├── README.md                   # This file└── services/

├── setup.ps1                   # Windows setup script    ├── auth_service/          # Authentication service

├── setup.sh                    # Linux/Mac setup script    ├── otp_service/           # OTP service

│    ├── payment_service/       # Payment service

├── gateway/                    # API Gateway (8000)    ├── notification_service/  # Notification service

│   ├── Dockerfile    └── tuition_service/       # Tuition service

│   ├── requirements.txt```

│   └── app/

│       ├── __init__.py## 🔧 Environment Variables

│       └── main.py            # Hello World + calls all services

│Each service can be configured using environment variables. See the `docker-compose.yml` file for the default configuration.

└── services/

    ├── auth_service/          # Port 8001### Database Configuration

    ├── otp_service/           # Port 8002- `DATABASE_URL`: PostgreSQL connection string

    ├── payment_service/       # Port 8003- Default: `postgresql://user:password@postgres:5432/{service_db}`

    ├── notification_service/  # Port 8004

    └── tuition_service/       # Port 8005### Redis Configuration

```- `REDIS_URL`: Redis connection string

- Default: `redis://redis:6379/0`

## 🧪 Testing Service Communication

### Service URLs (for Gateway)

1. **Start all services**: `docker-compose up --build`- `AUTH_SERVICE_URL`

- `OTP_SERVICE_URL`

2. **Test gateway calling all services**:- `PAYMENT_SERVICE_URL`

   ```bash- `NOTIFICATION_SERVICE_URL`

   curl http://localhost:8000/call-all- `TUITION_SERVICE_URL`

   ```

## 🧪 Testing the APIs

3. **Expected response**:

   ```jsonAll services provide interactive API documentation at `/docs` endpoint.

   {

     "gateway": "Hello from Gateway!",### Example: Testing Auth Service

     "services_called": {

       "auth": {"message": "Hello World from Auth Service!", "service": "auth_service"},1. Navigate to http://localhost:8001/docs

       "otp": {"message": "Hello World from OTP Service!", "service": "otp_service"},2. Try the `/register` endpoint with this payload:

       "payment": {"message": "Hello World from Payment Service!", "service": "payment_service"},```json

       "notification": {"message": "Hello World from Notification Service!", "service": "notification_service"},{

       "tuition": {"message": "Hello World from Tuition Service!", "service": "tuition_service"}  "email": "test@example.com",

     }  "username": "testuser",

   }  "password": "testpass123",

   ```  "full_name": "Test User"

}

## 🔧 Environment Variables```



Each service uses these environment variables:### Example: Testing via Gateway

- `MONGODB_URL`: MongoDB connection string

- `*_SERVICE_URL`: URLs for other services```bash

# Test gateway health

## 📝 Service Communication Flowcurl http://localhost:8000/health



```# Test auth service via gateway

Gateway → Auth → OTP → Notification → Tuition → Payment → (back to) Authcurl http://localhost:8000/auth/test

``````



Each service has a `/call-*` endpoint to test calling another service.## 📦 Technology Stack



## 🛠️ Local Development- **Framework**: FastAPI

- **Server**: Uvicorn

### Setup Virtual Environment- **Database**: PostgreSQL

- **Cache**: Redis

```powershell- **Containerization**: Docker & Docker Compose

# Windows- **Language**: Python 3.11

python -m venv .venv

.\.venv\Scripts\activate## 🔐 Security Notes

pip install -r requirements.txt

⚠️ **Important**: This is a test/development setup. For production:

# Linux/Mac

python3 -m venv .venv1. Change all default passwords

source .venv/bin/activate2. Use proper secret management (not environment variables)

pip install -r requirements.txt3. Implement proper authentication/authorization

```4. Use HTTPS/TLS

5. Add rate limiting

### Run Service Locally6. Implement proper logging and monitoring



```powershell## 📝 API Documentation

uvicorn app.main:app --reload --port 8000

```Each service has its own OpenAPI documentation available at the `/docs` endpoint. The interactive documentation allows you to:



## 🐛 Troubleshooting- View all available endpoints

- See request/response schemas

### Port already in use- Test endpoints directly from the browser

```powershell

# Windows - Find and kill process## 🤝 Contributing

netstat -ano | findstr :8000

taskkill /PID <pid> /F1. Fork the repository

```2. Create your feature branch

3. Commit your changes

### Docker issues4. Push to the branch

```bash5. Create a Pull Request

# Rebuild containers

docker-compose build --no-cache## 📄 License



# View logsThis project is for educational purposes.

docker-compose logs -f [service_name]

## 🐛 Troubleshooting

# Restart specific service

docker-compose restart [service_name]### Port already in use

```If you get a port conflict error, you can change the ports in `docker-compose.yml` or stop the conflicting service.



### MongoDB connection issues### Database connection issues

```bashMake sure PostgreSQL container is running:

# Check if MongoDB is running```bash

docker-compose ps mongodbdocker-compose ps postgres

```

# View MongoDB logs

docker-compose logs mongodb### Service not responding

```Check service logs:

```bash

## 📞 Supportdocker-compose logs [service_name]

```

For issues:

1. Check service logs: `docker-compose logs -f`## 📞 Support

2. Verify all containers are running: `docker-compose ps`

3. Test individual services before testing inter-service communicationFor issues and questions, please create an issue in the repository.


---

**🎉 All services are simple Hello World APIs with inter-service calling capability!**
