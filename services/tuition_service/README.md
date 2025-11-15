# Tuition Service

Student tuition management service with MongoDB. Handles tuition records, payments tracking, and student financial information in Vietnamese Dong (VND).

## Features

- 📊 Fetch all tuition records for a student
- 💰 Track tuition payments in Vietnamese Dong (VND)
- 📅 Monitor payment due dates and status
- 🎓 Manage semester-based tuition records
- 🔒 **JWT Authentication** - Secure access to tuition data
- 🛡️ **Access Control** - Students can only view their own records

## Endpoints

### Tuition Management (🔒 Authentication Required)
- `GET /api/tuition/{studentId}` - Get all tuition records for a student
  - **Requires:** Valid JWT Bearer token
  - **Access:** Students can only access their own records; Admins can access all
- `GET /api/tuition/record/{tuitionId}` - Get specific tuition record by ID
  - **Requires:** Valid JWT Bearer token
  - **Access:** Students can only access their own records
- `GET /api/tuition/` - Service information (Public)

### System
- `GET /` - Service status (Public)
- `GET /health` - Health check (Public)

## Running

### Docker
```bash
docker-compose up tuition_service
```

### Local Development

1. Activate virtual environment:
```bash
cd services/tuition_service
.\.venv\Scripts\activate
```

2. Run the service:
```bash
uvicorn app.main:app --reload --port 8005
```

## Database Setup

### Insert Sample Data

Run the sample data insertion script to populate the database with test data:

```bash
python insert_sample_tuition.py
```

This will create sample tuition records for 5 students with various payment statuses (pending, paid, partial).

## Testing

### Authentication Flow

1. **Login to get JWT token** (from Auth Service):
```bash
curl -X POST http://localhost:8002/api/auth/login \
  -H "Content-Type: application/json" \
  -H "x-api-key: bankwesen-api-key-2024-secure-change-in-production" \
  -d '{
    "username": "student1",
    "password": "password123"
  }'
```

2. **Use the token to access tuition data**:
```bash
# Get all tuition records for student (replace {TOKEN} with actual token)
curl http://localhost:8005/api/tuition/523K0001 \
  -H "Authorization: Bearer {TOKEN}" \
  -H "x-api-key: bankwesen-api-key-2024-secure-change-in-production"

# Get specific tuition record
curl http://localhost:8005/api/tuition/record/TU2024110001 \
  -H "Authorization: Bearer {TOKEN}" \
  -H "x-api-key: bankwesen-api-key-2024-secure-change-in-production"
```

### Sample Students in Database
After running `insert_sample_tuition.py`, the following students are available:

- **523K0001** - Nguyen Van A (Multiple semesters, mixed status)
- **523K0002** - Tran Thi B (Partial payment)
- **523K0003** - Le Van C (All paid)
- **523K0004** - Pham Thi D (International program, pending)
- **523K0005** - Hoang Van E (Overdue payment)

## Currency

All amounts are in **Vietnamese Dong (VND)**. Typical tuition fees range from 10-20 million VND per semester.

## Data Model

### Tuition Record
```json
{
  "tuitionId": "TU2024110001",
  "studentId": "523K0001",
  "studentName": "Nguyen Van A",
  "studentEmail": "nguyenvana@student.edu.vn",
  "semester": "Semester I",
  "academic_year": "2024-2025",
  "tuition_amount": 15000000.00,
  "due_date": "2024-12-31T23:59:59",
  "status": "pending",
  "created_at": "2024-11-15T10:00:00"
}
```

### Status Values
- `pending` - Payment not yet made
- `partial` - Partially paid
- `paid` - Fully paid

## Database
- MongoDB: `tuition_db`
- Collections: `Tuition`

## API Documentation
- Swagger UI: http://localhost:8005/docs
- ReDoc: http://localhost:8005/redoc

## Configuration

Environment variables (`.env`):
```env
# MongoDB Configuration
MONGODB_URL=mongodb+srv://...
DATABASE_NAME=tuition_db

# JWT Configuration (must match auth service)
JWT_SECRET_KEY=your-secret-key-here-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Key Configuration
API_KEY=bankwesen-api-key-2024-secure-change-in-production
ENABLE_API_KEY=true

# Service Configuration
SERVICE_NAME=Tuition Service
SERVICE_PORT=8005
```

## Security

### Authentication
All tuition endpoints require **TWO** authentication headers:
1. **JWT Bearer Token** - From Auth Service (`/api/auth/login`)
   - Must be included in `Authorization` header as `Bearer {token}`
2. **API Key** - Service-level authentication
   - Must be included in `x-api-key` header

### Access Control
- **Students**: Can view ANY student's tuition records
  - Allows students to help pay for each other's tuition fees
  - Common use case: Friends or family members assisting with tuition payments
  - Requires valid authentication (JWT token + API key)
- **Admins**: Full access to all tuition records
  - Identified by `role: admin` in the JWT token

### ⚠️ IMPORTANT: JWT Configuration
The JWT secret key in `tuition_service/.env` **MUST match** the secret key in `auth_service/.env`:

```bash
# auth_service/.env
SECRET_KEY=your-secret-key-change-this-in-production-min-32-chars

# tuition_service/.env (MUST BE THE SAME VALUE)
JWT_SECRET_KEY=your-secret-key-change-this-in-production-min-32-chars
```

### Error Responses
- `401 Unauthorized`: Missing, invalid, or expired JWT token (check if JWT secrets match!)
- `403 Forbidden`: Invalid API key or not authenticated
- `404 Not Found`: Student or tuition record doesn't exist

### Use Cases
**Why students can view other students' tuition?**
- 🤝 **Mutual Support**: Students can help friends with tuition payments
- 👨‍👩‍👧‍👦 **Family Assistance**: Parents/siblings can check and pay tuition
- 💰 **Group Payments**: Study groups can collectively manage tuition obligations
- 🎓 **Scholarship Programs**: Student organizations can verify and assist with tuition
