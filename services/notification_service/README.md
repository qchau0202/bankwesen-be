# Notification Service

Notification management service with MongoDB.

## Endpoints

- `GET /` - Service info
- `GET /hello` - Hello World
- `GET /health` - Health check
- `GET /call-tuition` - Call Tuition service (test inter-service communication)

## Running

### Docker
```bash
docker-compose up notification_service
```

### Local
```bash
cd services/notification_service
.\.venv\Scripts\activate
uvicorn app.main:app --reload --port 8004
```

## Testing

```bash
# Hello World
curl http://localhost:8004/hello

# Call Tuition service
curl http://localhost:8004/call-tuition
```

## Database
- MongoDB: `mongodb://mongodb:27017/notification_db`

## API Docs
http://localhost:8004/docs
