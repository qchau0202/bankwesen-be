# OTP Service# OTP Service



One-Time Password service with MongoDB.One-Time Password microservice for the Bankwesen banking system.



## Endpoints## 🎯 Purpose



- `GET /` - Service infoHandles:

- `GET /hello` - Hello World- OTP generation for email/SMS

- `GET /health` - Health check- OTP verification

- `GET /call-notification` - Call Notification service (test inter-service communication)- OTP expiration management

- OTP revocation

## Running

## 🚀 Running the Service

### Docker

```bash### With Docker

docker-compose up otp_service

``````bash

# From project root

### Localdocker-compose up otp_service

```bash

cd services/otp_service# Or build and run individually

.\.venv\Scripts\activatecd services/otp_service

uvicorn app.main:app --reload --port 8002docker build -t bankwesen-otp .

```docker run -p 8002:8002 bankwesen-otp

```

## Testing

### Local Development

```bash

# Hello World```bash

curl http://localhost:8002/hello# Navigate to OTP service directory

cd services/otp_service

# Call Notification service

curl http://localhost:8002/call-notification# Create virtual environment

```python -m venv .venv



## Database# Activate virtual environment (Windows)

- MongoDB: `mongodb://mongodb:27017/otp_db`.venv\Scripts\activate



## API Docs# Activate virtual environment (Linux/Mac)

http://localhost:8002/docssource .venv/bin/activate


# Install dependencies
pip install -r requirements.txt

# Run the service
uvicorn app.main:app --reload --port 8002
```

## 📡 Endpoints

### Core Endpoints

- **GET** `/` - Service information
- **GET** `/health` - Health check
- **GET** `/test` - Test endpoint

### OTP Operations

- **POST** `/generate` - Generate OTP
  ```json
  {
    "email": "user@example.com",
    "purpose": "verification"
  }
  ```
  Response includes OTP code (for testing only)

- **POST** `/verify` - Verify OTP
  ```json
  {
    "email": "user@example.com",
    "otp_code": "123456"
  }
  ```

- **DELETE** `/revoke/{email}` - Revoke OTP for email

## 📚 API Documentation

Interactive API docs available at:
- Swagger UI: http://localhost:8002/docs
- ReDoc: http://localhost:8002/redoc

## 🧪 Testing

### Via Gateway
```bash
curl http://localhost:8000/otp/test
```

### Direct Access
```bash
# Health check
curl http://localhost:8002/health

# Generate OTP
curl -X POST http://localhost:8002/generate \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "purpose": "verification"
  }'

# Verify OTP (use code from generate response)
curl -X POST http://localhost:8002/verify \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "otp_code": "123456"
  }'

# Revoke OTP
curl -X DELETE http://localhost:8002/revoke/test@example.com
```

## 📦 Dependencies

See `requirements.txt`:
- fastapi - Web framework
- uvicorn - ASGI server
- pydantic - Data validation
- redis - Cache for OTP storage

## 🗄️ Storage

Uses Redis for temporary OTP storage:
```
REDIS_URL=redis://redis:6379/0
```

### OTP Structure

```python
{
  "email@example.com": {
    "code": "123456",
    "expires_at": "2024-01-01T12:00:00",
    "purpose": "verification"
  }
}
```

## ⏰ OTP Specifications

- **Length**: 6 digits
- **Expiration**: 10 minutes
- **Purpose**: Configurable (verification, login, etc.)
- **Storage**: In-memory (testing) / Redis (production)

## 🔧 Environment Variables

```env
REDIS_URL=redis://redis:6379/0
```

## 📝 Notes

⚠️ **Current Implementation**: 
- Uses in-memory storage (dict) for testing
- OTP is returned in response for easy testing
- No actual email/SMS sending

🚀 **Production Considerations**:
- Integrate with Redis for distributed storage
- Implement email service (SendGrid, AWS SES)
- Implement SMS service (Twilio, AWS SNS)
- Remove OTP from response
- Add rate limiting
- Add attempt tracking
- Implement backup codes
- Add logging and monitoring

## 🔐 Security Features

- OTP expiration (10 minutes)
- Single-use codes (deleted after verification)
- Email validation
- CORS middleware

## 🌐 Integration

Commonly used with:
- Auth Service (2FA)
- Password reset flows
- Transaction verification
- Account verification
