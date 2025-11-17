# Database initialization script for Docker setup (Windows)

Write-Host "Waiting for services to be ready..." -ForegroundColor Cyan
Start-Sleep -Seconds 10

Write-Host "Initializing Auth Service database..." -ForegroundColor Green
docker exec bankwesen_auth_service python -c @"
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime
import os

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

async def init_auth():
    client = AsyncIOMotorClient(os.getenv('MONGODB_URL', 'mongodb://mongodb:27017'))
    db = client['auth_db']
    users = db['User']
    
    # Clear existing
    await users.delete_many({})
    
    # Create test users
    test_users = [
        {
            'userid': '523K0001',
            'username': 'student1',
            'password_hash': pwd_context.hash('password123'),
            'full_name': 'Nguyen Van A',
            'email': 'student1@university.edu',
            'phone_number': '0901234567',
            'balance': 5000000.0,
            'created_at': datetime.utcnow()
        },
        {
            'userid': '523K0002',
            'username': 'student2',
            'password_hash': pwd_context.hash('password123'),
            'full_name': 'Tran Thi B',
            'email': 'student2@university.edu',
            'phone_number': '0902234567',
            'balance': 3000000.0,
            'created_at': datetime.utcnow()
        }
    ]
    
    await users.insert_many(test_users)
    print(f'Inserted {len(test_users)} test users')
    client.close()

asyncio.run(init_auth())
"@

Write-Host "Initializing Tuition Service database..." -ForegroundColor Green
docker exec bankwesen_tuition_service python -c @"
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta, timezone
import os

UTC_PLUS_7 = timezone(timedelta(hours=7))

async def init_tuition():
    client = AsyncIOMotorClient(os.getenv('MONGODB_URL', 'mongodb://mongodb:27017'))
    db = client['tuition_db']
    tuition = db['Tuition']
    
    # Clear existing
    await tuition.delete_many({})
    
    now = datetime.now(UTC_PLUS_7)
    
    # Create sample tuition records
    sample_data = []
    for i in range(1, 6):
        for j in range(1, 3):
            sample_data.append({
                'tuitionId': f'TU202411{str(i).zfill(3)}{j}',
                'studentId': f'523K{str(i).zfill(4)}',
                'studentName': f'Student {i}',
                'studentEmail': f'student{i}@university.edu',
                'semester': f'Semester {\"I\" if j == 1 else \"II\"}',
                'academic_year': '2024-2025',
                'tuition_amount': 10000000 + i * 1000000 + j * 500000,
                'due_date': now + timedelta(days=30 * j),
                'payment_status': 'pending' if i % 2 == 1 else 'paid',
                'created_at': now,
                'updated_at': now
            })
    
    await tuition.insert_many(sample_data)
    print(f'Inserted {len(sample_data)} tuition records')
    client.close()

asyncio.run(init_tuition())
"@

Write-Host "Database initialization complete!" -ForegroundColor Green
