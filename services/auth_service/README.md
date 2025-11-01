# Auth Service

Authentication service with MongoDB.

## Endpoints

- `GET /` - Service info
- `GET /hello` - Hello World
- `GET /health` - Health check
- `GET /call-otp` - Call OTP service (test inter-service communication)

## Running

### Docker
```bash
docker-compose up auth_service
```

### Local
```bash
cd services/auth_service
.\.venv\Scripts\activate
uvicorn app.main:app --reload --port 8001
```

## Testing

```bash
# Hello World
curl http://localhost:8001/hello

# Call OTP service
curl http://localhost:8001/call-otp
```

## Database
- MongoDB: `mongodb://mongodb:27017/auth_db`

## API Docs
http://localhost:8001/docs
