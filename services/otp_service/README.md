# OTP Service

OTP (One-Time Password) Service for payment verification using Redis.

## Overview

The OTP Service manages one-time password generation, verification, and lifecycle for payment transactions. It uses Redis for fast, temporary storage of OTP data with automatic expiration.

## Features

- **OTP Generation**: Generate 6-digit OTP codes with 60-second expiration
- **OTP Verification**: Verify OTP codes with attempt tracking
- **OTP Resend**: Resend expired OTPs
- **Payment Locking**: Lock payments after 3 failed attempts (5-minute lockout)
- **Redis-backed Storage**: Fast, temporary storage with automatic expiration

## Endpoints

### Base URL: `/api/otp`

#### 1. Request OTP
```http
POST /api/otp/request
```

**Request Body:**
```json
{
  "payment_id": "pay_123",
  "tuition_id": "tuition_456",
  "user_id": "user_789",
  "amount": 1000.00,
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "message": "OTP generated successfully. Check your email.",
  "payment_id": "pay_123",
  "expires_in": 60,
  "attempts_remaining": 3
}
```

#### 2. Verify OTP
```http
POST /api/otp/verify
```

**Request Body:**
```json
{
  "payment_id": "pay_123",
  "otp_code": "123456"
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "OTP verified successfully",
  "payment_id": "pay_123",
  "verified": true,
  "attempts_remaining": null,
  "locked": false
}
```

**Response (Failed - Invalid OTP):**
```json
{
  "success": false,
  "message": "Invalid OTP code. 2 attempts remaining.",
  "payment_id": "pay_123",
  "verified": false,
  "attempts_remaining": 2,
  "locked": false
}
```

**Response (Failed - Locked):**
```json
{
  "success": false,
  "message": "Maximum attempts reached. Payment is locked.",
  "payment_id": "pay_123",
  "verified": false,
  "attempts_remaining": 0,
  "locked": true
}
```

#### 3. Resend OTP
```http
POST /api/otp/resend
```

**Request Body:**
```json
{
  "payment_id": "pay_123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "OTP resent successfully. Check your email.",
  "payment_id": "pay_123",
  "expires_in": 60,
  "attempts_remaining": 3
}
```

#### 4. Get OTP Status
```http
GET /api/otp/{payment_id}/status
```

**Response:**
```json
{
  "success": true,
  "message": "OTP is active",
  "payment_id": "pay_123",
  "expires_in": 45,
  "attempts_remaining": 3
}
```

#### 5. Cancel OTP
```http
DELETE /api/otp/{payment_id}
```

**Response:** `204 No Content`

## Payment Flow Integration

### 3.1 Create Payment
```
Payment Service -> OTP Service
POST /api/otp/request
```

### 3.2 OTP Request
```
User requests OTP -> System generates OTP (60s expiration)
POST /api/payment/{paymentID}/otp -> POST /api/otp/request
```

### 3.3 OTP Verification
```
User inputs OTP -> System verifies
POST /api/payment/{paymentID}/verify-otp -> POST /api/otp/verify
```

**Success Flow:**
```
OTP Verified -> Create Transaction -> Return Payment Details
POST /api/otp/verify -> POST /api/transaction -> GET /api/payment/{paymentID}
```

**Failure Flows:**

1. **Expired OTP:**
```
User clicks resend -> Generate new OTP
POST /api/payment/{paymentID}/otp -> POST /api/otp/resend
```

2. **Wrong OTP (Max 3 attempts):**
```
3 failed attempts -> Payment locked -> Cancel payment
POST /api/payment/{paymentID}/cancel
```

## Redis Data Structure

### OTP Data
**Key:** `otp:{payment_id}`
**Expiration:** 60 seconds
**Value:**
```json
{
  "otp_code": "123456",
  "payment_id": "pay_123",
  "tuition_id": "tuition_456",
  "user_id": "user_789",
  "amount": 1000.00,
  "attempts": 0,
  "created_at": "2025-11-15T10:30:00",
  "email": "user@example.com"
}
```

### Attempts Counter
**Key:** `otp_attempts:{payment_id}`
**Expiration:** 300 seconds (5 minutes)
**Value:** Integer (0-3)

### Payment Lock
**Key:** `otp_lock:{payment_id}`
**Expiration:** 300 seconds (5 minutes)
**Value:** "locked"

## Configuration

Environment variables (`.env` or docker-compose):

```env
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379

OTP_LENGTH=6
OTP_EXPIRATION=60
OTP_MAX_ATTEMPTS=3
OTP_ATTEMPT_WINDOW=300

NOTIFICATION_SERVICE_URL=http://notification_service:8004
```

## Running the Service

### With Docker Compose
```bash
docker-compose up otp_service redis
```

### Standalone
```bash
cd services/otp_service
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8002
```

## Testing the Service

### Using curl

1. **Request OTP:**
```bash
curl -X POST http://localhost:8002/api/otp/request \
  -H "Content-Type: application/json" \
  -d '{
    "payment_id": "pay_123",
    "tuition_id": "tuition_456",
    "user_id": "user_789",
    "amount": 1000.00,
    "email": "user@example.com"
  }'
```

2. **Verify OTP:**
```bash
curl -X POST http://localhost:8002/api/otp/verify \
  -H "Content-Type: application/json" \
  -d '{
    "payment_id": "pay_123",
    "otp_code": "123456"
  }'
```

3. **Resend OTP:**
```bash
curl -X POST http://localhost:8002/api/otp/resend \
  -H "Content-Type: application/json" \
  -d '{
    "payment_id": "pay_123"
  }'
```

## Dependencies

- FastAPI 0.104.1
- Redis 5.0.1
- Pydantic Settings 2.1.0
- Uvicorn 0.24.0
- HTTPx 0.25.1

## Security Considerations

1. **OTP Expiration**: OTPs expire after 60 seconds
2. **Attempt Limiting**: Maximum 3 verification attempts
3. **Payment Locking**: Payments locked for 5 minutes after max attempts
4. **Automatic Cleanup**: Redis automatically removes expired data
5. **Secure Storage**: OTP codes stored in Redis with encryption in transit

## Architecture

```
┌─────────────────┐
│  Payment Service│
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌─────────────────┐
│   OTP Service   │◄────►│      Redis      │
└────────┬────────┘      └─────────────────┘
         │
         ▼
┌─────────────────┐
│Notification Svc │
└─────────────────┘
```

## Future Enhancements

- [ ] Email/SMS notification integration
- [ ] Configurable OTP length and expiration
- [ ] Support for multiple OTP delivery methods
- [ ] OTP usage analytics and monitoring
- [ ] Rate limiting per user/payment
- [ ] Multi-factor authentication support
