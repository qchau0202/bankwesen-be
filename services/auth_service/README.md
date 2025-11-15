# Auth Service

Authentication service with MongoDB Atlas (online database).

## 🔧 Setup

### 1. Configure Environment Variables
Make sure `.env` file exists with your MongoDB credentials and API key:
```env
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/
DATABASE_NAME=auth_db
SECRET_KEY=your-secret-key-here
API_KEY=your-secure-api-key-here
ENABLE_API_KEY=true
```

### 2. Install Dependencies
```bash
cd services/auth_service
pip install -r requirements.txt
```

### 3. Insert Test Users (Required - First Time Only)
This script will create test users with **securely hashed passwords** using bcrypt:
```bash
python insert_test_users.py
```

**Note**: Run this script whenever you need to reset the test users or after changing the database.

## 🚀 Running

### Local Development (Recommended for testing)
```bash
cd services/auth_service
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### Docker
```bash
# From project root
docker-compose up auth_service
```

## 📌 API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login (requires API key)
- `POST /api/v1/auth/register` - User registration (requires API key)
- `GET /api/v1/auth/me` - Get current user info
- `GET /api/v1/auth/verify` - Verify token

### Health Check
- `GET /` - Service info
- `GET /health` - Health check
- `GET /hello` - Hello World

## 🧪 Testing

### Login (requires API key)
```bash
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -H "X-API-Key: bankwesen-api-key-2024-secure-change-in-production" \
  -d '{"username":"student1","password":"password123"}'
```

### Register (requires API key)
```bash
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -H "X-API-Key: bankwesen-api-key-2024-secure-change-in-production" \
  -d '{
    "username":"newuser",
    "password":"password123",
    "confirm_password":"password123",
    "full_name":"John Doe",
    "email":"john@example.com",
    "phone_number":"1234567890"
  }'
```

### Health Check (No API key required)
```bash
curl http://localhost:8001/health
```

## 📚 API Documentation
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## 🔐 Test Users
After running `insert_test_users.py`, you can login with:
- **Student**: `student1` / `password123`
- **Student**: `student2` / `password123`
- **Staff**: `staff1` / `staff123`
- **Admin**: `admin` / `admin123`

**Security**: All passwords are hashed with bcrypt before storing in the database.

## 🔑 API Key Protection

The auth service requires an API key for authentication endpoints to prevent unauthorized access.

### Configuration
Set in `.env` file:
```env
API_KEY=your-secure-api-key-here
API_KEY_NAME=X-API-Key
ENABLE_API_KEY=true
```

### Usage
Include the API key in request headers:
```bash
X-API-Key: your-api-key-here
```

### Example with curl:
```bash
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -H "X-API-Key: bankwesen-api-key-2024-secure-change-in-production" \
  -d '{"username":"student1","password":"password123"}'
```

### Example with JavaScript (Fetch):
```javascript
fetch('http://localhost:8001/api/v1/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'bankwesen-api-key-2024-secure-change-in-production'
  },
  body: JSON.stringify({
    username: 'student1',
    password: 'password123'
  })
});
```

### Disable API Key (Development Only)
Set `ENABLE_API_KEY=false` in `.env` to disable API key checking.

## 🌐 CORS Configuration
CORS is configured in `.env` file. Update `ALLOWED_ORIGINS` to match your frontend URL:
```env
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

## 🗄️ Database
- **Type**: MongoDB Atlas (Online)
- **Database**: auth_db
- **Collection**: User
