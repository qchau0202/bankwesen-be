# Auth Service

Authentication service with MongoDB Atlas (online database).

## 🔧 Setup

### 1. Configure Environment Variables
Make sure `.env` file exists with your MongoDB credentials:
```env
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/
DATABASE_NAME=auth_db
SECRET_KEY=your-secret-key-here
```

### 2. Install Dependencies
```bash
cd services/auth_service
pip install -r requirements.txt
```

### 3. Insert Test Users
```bash
python insert_test_users.py
```

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
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Get current user info
- `GET /api/v1/auth/verify` - Verify token

### Health Check
- `GET /` - Service info
- `GET /health` - Health check
- `GET /hello` - Hello World

## 🧪 Testing

```bash
# Test login
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"student1","password":"password123"}'

# Health check
curl http://localhost:8001/health
```

## 📚 API Documentation
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## 🔐 Test Users
- **Student**: `student1` / `password123`
- **Staff**: `staff1` / `staff123`
- **Admin**: `admin` / `admin123`

## 🌐 CORS Configuration
CORS is configured in `.env` file. Update `ALLOWED_ORIGINS` to match your frontend URL:
```env
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

## 🗄️ Database
- **Type**: MongoDB Atlas (Online)
- **Database**: auth_db
- **Collection**: User
