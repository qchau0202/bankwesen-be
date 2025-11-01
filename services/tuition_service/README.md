# Tuition Service

Tuition fee management service with MongoDB.

## Endpoints

- `GET /` - Service info
- `GET /hello` - Hello World
- `GET /health` - Health check
- `GET /call-payment` - Call Payment service (test inter-service communication)

## Running

### Docker
```bash
docker-compose up tuition_service
```

### Local
```bash
cd services/tuition_service
.\.venv\Scripts\activate
uvicorn app.main:app --reload --port 8005
```

## Testing

```bash
# Hello World
curl http://localhost:8005/hello

# Call Payment service
curl http://localhost:8005/call-payment
```

## Database
- MongoDB: `mongodb://mongodb:27017/tuition_db`

## API Docs
http://localhost:8005/docs
