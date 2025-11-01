# Gateway Service

API Gateway that routes requests to all microservices.

## Endpoints

- `GET /` - Service info
- `GET /hello` - Hello World
- `GET /health` - Health check
- `GET /call-all` - Call all services (test inter-service communication)

## Running

### Docker
```bash
docker-compose up gateway
```

### Local
```bash
cd gateway
.\.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

## Testing

```bash
# Hello World
curl http://localhost:8000/hello

# Call all services
curl http://localhost:8000/call-all
```

## API Docs
http://localhost:8000/docs
