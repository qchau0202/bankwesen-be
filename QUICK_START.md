# Bankwesen Backend - Quick Start Guide

Complete banking system with microservices architecture. One-click setup with Docker Compose.

## Quick Start (Recommended)

### Prerequisites
- Docker & Docker Compose installed
- Git

### One-Click Run

**Windows:**
```powershell
git clone <repository-url>
cd bankwesen-be
docker-compose up --build -d
.\init-db.ps1
```

**Linux/Mac:**
```bash
git clone <repository-url>
cd bankwesen-be
docker-compose up --build -d
./init-db.sh
```

That's it! All services will be running on:
- **Gateway**: http://localhost:8000
- **Auth Service**: http://localhost:8001
- **OTP Service**: http://localhost:8002
- **Payment Service**: http://localhost:8003
- **Notification Service**: http://localhost:8004
- **Tuition Service**: http://localhost:8005

## API Documentation

Access Swagger UI for each service:
- Gateway: http://localhost:8000/docs
- Auth: http://localhost:8001/docs
- OTP: http://localhost:8002/docs
- Payment: http://localhost:8003/docs
- Notification: http://localhost:8004/docs
- Tuition: http://localhost:8005/docs

## Test Credentials

After running `init-db.ps1` or `init-db.sh`, you can login with:

| Username  | Password     | User ID  | Balance    |
|-----------|--------------|----------|------------|
| student1  | password123  | 523K0001 | 5,000,000 VND |
| student2  | password123  | 523K0002 | 3,000,000 VND |

## Quick API Test

### 1. Login
```bash
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -H "x-api-key: bankwesen-api-key-2024-secure-change-in-production" \
  -d '{
    "username": "student1",
    "password": "password123"
  }'
```

Save the `access_token` from response.

### 2. View Tuition
```bash
curl -X GET http://localhost:8005/api/tuition/523K0001 \
  -H "Authorization: Bearer <your-token>" \
  -H "x-api-key: bankwesen-api-key-2024-secure-change-in-production"
```

### 3. View Other Student's Tuition (Payment Assistance)
```bash
curl -X GET http://localhost:8005/api/tuition/523K0002 \
  -H "Authorization: Bearer <your-token>" \
  -H "x-api-key: bankwesen-api-key-2024-secure-change-in-production"
```

## Sample Data Included

After initialization:
- **2 test users** (student1, student2)
- **10 tuition records** for 5 students
- **Multiple semesters** with different payment statuses
- **Total tuition**: ~150 million VND

## Management Commands

### Stop All Services
```bash
docker-compose down
```

### Stop and Remove Volumes (Reset Database)
```bash
docker-compose down -v
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f tuition_service
```

### Restart a Service
```bash
docker-compose restart tuition_service
```

### Rebuild After Code Changes
```bash
docker-compose up --build
```

## Development Setup (Without Docker)

If you want to run services locally:

**Windows:**
```powershell
.\setup.ps1
```

**Linux/Mac:**
```bash
chmod +x setup.sh
./setup.sh
```

Then run each service individually:
```bash
cd services/auth_service
.\.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate      # Linux/Mac
uvicorn app.main:app --reload --port 8001
```

## Architecture

```
┌─────────────┐
│   Gateway   │ :8000
└──────┬──────┘
       │
   ┌───┴────┬────────┬──────────┬────────────┐
   │        │        │          │            │
┌──▼──┐  ┌─▼──┐  ┌─▼───┐  ┌───▼────┐  ┌───▼────┐
│Auth │  │OTP │  │Pay  │  │Notify  │  │Tuition │
│8001 │  │8002│  │8003 │  │8004    │  │8005    │
└──┬──┘  └─┬──┘  └─┬───┘  └───┬────┘  └───┬────┘
   │       │       │          │            │
   └───────┴───────┴──────────┴────────────┘
                   │
              ┌────┴─────┐
              │          │
          ┌───▼──┐   ┌──▼───┐
          │Mongo │   │Redis │
          │27017 │   │6379  │
          └──────┘   └──────┘
```

## Security Features

- **JWT Authentication**: Token-based user authentication
- **API Key Protection**: Service-level authentication
- **Role Removed**: Simplified authentication without role-based access
- **Cross-Student Access**: Students can help pay for each other's tuition

## Troubleshooting

### Services not starting
```bash
# Check logs
docker-compose logs

# Restart
docker-compose restart
```

### Database connection issues
```bash
# Ensure MongoDB is running
docker-compose ps mongodb

# Reinitialize
docker-compose down -v
docker-compose up -d
.\init-db.ps1  # or ./init-db.sh
```

### Port conflicts
Check if ports 8000-8005, 27017, 6379 are available.

## Environment Variables

Each service has an `.env` file. For Docker, these are overridden in `docker-compose.yml` to use local MongoDB/Redis.

Key variables:
- `MONGODB_URL`: Database connection string
- `JWT_SECRET_KEY`: Must match across services
- `API_KEY`: Service authentication key

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes
4. Test with `docker-compose up --build`
5. Submit pull request

## License

[Your License Here]

## Support

[Your Contact Information]
