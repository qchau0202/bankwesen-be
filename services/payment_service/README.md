# Payment Service

Payment processing service with MongoDB.

## Endpoints

- `GET /` - Service info
- `GET /hello` - Hello World
- `GET /health` - Health check
- `GET /call-auth` - Call Auth service (test inter-service communication)

## Running

### Docker
```bash
docker-compose up payment_service
```

### Local
```bash
cd services/payment_service
.\.venv\Scripts\activate
uvicorn app.main:app --reload --port 8003
```

## Testing

```bash
# Hello World
curl http://localhost:8003/hello

# Call Auth service
curl http://localhost:8003/call-auth
```

## Database
- MongoDB: `mongodb://mongodb:27017/payment_db`

## API Docs
http://localhost:8003/docs
