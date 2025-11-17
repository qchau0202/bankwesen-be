# Payment Service

Payment processing service with OTP verification and secure payment flow for tuition payments.

## Features

- **Secure Payment Processing** - API Key authentication for all endpoints
- **OTP Verification** - 60-second OTP with email delivery via internal OTP service
- **Idempotency** - Prevents duplicate payments using idempotency keys
- **Payment Locking** - Only one payment allowed per tuition per customer
- **Attempt Limiting** - Maximum 3 OTP verification attempts
- **Message Broker** - Notifies other services of payment events
- **Transaction Safety** - Try-catch blocks for transaction processing

## Payment Flow

### 3.1 Create Payment
1. User confirms tuition details
2. POST `/api/payment/` → Creates payment with pending status
3. Message broker notifies other services
4. Payment is locked for this tuition/customer combination

### 3.2 Request OTP
1. POST `/api/payment/{paymentID}/otp` → Generates OTP
2. OTP sent to customer email (60s expiration)
3. User receives OTP code

### 3.3 Verify OTP
1. POST `/api/payment/{paymentID}/verify-otp` → Verifies OTP
2. **SUCCESS**: 
   - Updates tuition status to "paid"
   - Completes payment
   - Returns payment details
3. **FAILED**:
   - **EXPIRED**: User can resend OTP
   - **WRONG OTP**: User can retry (max 3 attempts)
   - **MAX ATTEMPTS**: Payment auto-cancelled, must restart from 3.1

### 3.4 Cancel Payment
1. POST `/api/payment/{paymentID}/cancel` → Cancels payment
2. User must create new payment to retry

## API Endpoints

### Payment Management
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/payment/` | Create new payment | JWT + API Key |
| GET | `/api/payment/{paymentID}` | Get payment details | JWT + API Key |
| POST | `/api/payment/{paymentID}/otp` | Request OTP | JWT + API Key |
| POST | `/api/payment/{paymentID}/verify-otp` | Verify OTP & complete payment | JWT + API Key |
| POST | `/api/payment/{paymentID}/cancel` | Cancel payment | JWT + API Key |

### Health Checks
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Service information |
| GET | `/health` | Health check |

## Authentication

### API Key (Required)
All `/api/*` endpoints require API key in header:
```
x-api-key: your-api-key-here
```

### JWT Token (Required)
All `/api/*` endpoints require JWT token:
```
Authorization: Bearer your-jwt-token-here
```

## Request/Response Examples

### Create Payment
```bash
POST /api/payment/
Headers:
  x-api-key: your-api-key
  Authorization: Bearer jwt-token
Body:
{
  "customerId": "523K0000",
  "tuitionId": "TU1731369600001",
  "email": "student@example.com"
}

Response (201):
{
  "paymentId": "PAY1731369600001",
  "customerId": "523K0000",
  "tuitionId": "TU1731369600001",
  "idempotency_key": "unique-key",
  "amount": 5000000.00,
  "status": "pending",
  "otp_attempts": 0,
  "is_locked": false,
  "created_at": "2024-11-15T10:00:00",
  "expired_at": "2024-11-15T11:00:00"
}
```

### Request OTP
```bash
POST /api/payment/PAY1731369600001/otp
Headers:
  x-api-key: your-api-key
  Authorization: Bearer jwt-token
Body:
{
  "customerId": "523K0000",
  "tuitionId": "TU1731369600001",
  "email": "student@example.com"
}

Response (200):
{
  "success": true,
  "message": "OTP sent successfully",
  "payment_id": "PAY1731369600001",
  "expires_in": 60,
  "attempts_remaining": 3
}
```

### Verify OTP
```bash
POST /api/payment/PAY1731369600001/verify-otp
Headers:
  x-api-key: your-api-key
  Authorization: Bearer jwt-token
Body:
{
  "otp_code": "123456"
}

Response (200):
{
  "success": true,
  "message": "Payment completed successfully",
  "payment": {
    "paymentId": "PAY1731369600001",
    "status": "completed",
    ...
  }
}
```

## Environment Variables

```env
# MongoDB
MONGODB_URL=mongodb://mongodb:27017
DATABASE_NAME=payment_db

# JWT Settings
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Key
API_KEY=your-api-key
ENABLE_API_KEY=true

# Service Configuration
SERVICE_NAME=Payment Service
SERVICE_PORT=8003

# External Services
OTP_SERVICE_URL=http://otp_service:8004
TUITION_SERVICE_URL=http://tuition_service:8005
NOTIFICATION_SERVICE_URL=http://notification_service:8006
```

## Running the Service

### Docker
```bash
docker-compose up payment_service
```

### Local Development
```bash
cd services/payment_service
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8003
```

## Database Schema

### Payment Collection
```python
{
  "_id": ObjectId,
  "paymentId": str,           # Unique payment ID
  "customerId": str,          # Customer ID from auth service
  "tuitionId": str,           # Tuition ID
  "idempotency_key": str,     # Prevents duplicate payments
  "amount": float,            # Payment amount
  "status": str,              # pending, completed, failed, cancelled
  "otp_attempts": int,        # Number of OTP attempts (max 3)
  "is_locked": bool,          # Locked after max attempts
  "created_at": datetime,     # Payment creation time
  "expired_at": datetime      # Payment expiration time (60 min)
}
```

## Security Features

1. **API Key Authentication** - Protects all endpoints
2. **JWT Authorization** - Validates user identity
3. **Idempotency Keys** - Prevents duplicate payments
4. **Payment Locking** - One payment per tuition per customer
5. **OTP Verification** - Secure transaction confirmation
6. **Attempt Limiting** - Max 3 OTP attempts before lock
7. **Transaction Safety** - Try-catch for tuition updates

## Message Broker

The service uses a message broker to notify other services of payment events:
- `payment.created` - When payment is created
- `payment.completed` - When payment is completed
- `payment.cancelled` - When payment is cancelled
- `payment.failed` - When payment fails

*Note: Current implementation uses logging. Replace with actual broker (RabbitMQ, Kafka, etc.) in production.*

## API Documentation
- Swagger UI: http://localhost:8003/docs
- ReDoc: http://localhost:8003/redoc

## Testing

```bash
# Health check
curl http://localhost:8003/health

# Create payment (requires auth)
curl -X POST http://localhost:8003/api/payment/ \
  -H "x-api-key: your-key" \
  -H "Authorization: Bearer token" \
  -H "Content-Type: application/json" \
  -d '{"customerId":"523K0000","tuitionId":"TU001","email":"test@test.com"}'

# Get payment
curl http://localhost:8003/api/payment/PAY001 \
  -H "x-api-key: your-key" \
  -H "Authorization: Bearer token"
```

## Dependencies

- FastAPI - Web framework
- Motor - Async MongoDB driver
- HTTPx - HTTP client for internal API calls
- PyJWT - JWT token handling
- Pydantic - Data validation
- Email-Validator - Email validation

## Notes

- Transaction model removed (use payment history from payment collection)
- All internal service calls use API keys
- OTP expiration: 60 seconds
- Payment expiration: 60 minutes
- Max OTP attempts: 3
- Payment states: pending → completed/cancelled/failed
