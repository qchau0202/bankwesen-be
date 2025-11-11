# API Key Protection - Quick Reference

## 🔑 What is the API Key?

The API key is an additional security layer that prevents unauthorized access to your authentication endpoints. All clients must include a valid API key in their requests.

## 📝 Configuration

### .env File
```env
API_KEY=bankwesen-api-key-2024-secure-change-in-production
API_KEY_NAME=X-API-Key
ENABLE_API_KEY=true
```

### Change the API Key
1. Update `API_KEY` in `.env` file
2. Restart the service
3. Update all clients to use the new key

### Disable API Key (For Development Only)
Set `ENABLE_API_KEY=false` in `.env`

## 🌐 Frontend Integration

### React/JavaScript Example
```javascript
const API_KEY = 'bankwesen-api-key-2024-secure-change-in-production';

async function login(username, password) {
  const response = await fetch('http://localhost:8001/api/v1/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY
    },
    body: JSON.stringify({ username, password })
  });
  
  return await response.json();
}
```

### Axios Example
```javascript
import axios from 'axios';

const API_KEY = 'bankwesen-api-key-2024-secure-change-in-production';

// Configure axios defaults
axios.defaults.headers.common['X-API-Key'] = API_KEY;

// Or per request
axios.post('http://localhost:8001/api/v1/auth/login', {
  username: 'student1',
  password: 'password123'
}, {
  headers: {
    'X-API-Key': API_KEY
  }
});
```

### Python/Requests Example
```python
import requests

API_KEY = 'bankwesen-api-key-2024-secure-change-in-production'

response = requests.post(
    'http://localhost:8001/api/v1/auth/login',
    json={'username': 'student1', 'password': 'password123'},
    headers={'X-API-Key': API_KEY}
)
```

## 🧪 Testing

### Test with curl
```bash
# Valid API key - should succeed
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -H "X-API-Key: bankwesen-api-key-2024-secure-change-in-production" \
  -d '{"username":"student1","password":"password123"}'

# No API key - should fail with 401
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"student1","password":"password123"}'

# Invalid API key - should fail with 403
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -H "X-API-Key: wrong-key" \
  -d '{"username":"student1","password":"password123"}'
```

### Test with Python script
```bash
python test_api_key.py
```

## 🔒 Security Best Practices

1. **Never commit API keys to git**
   - Use `.env` file (already in `.gitignore`)
   - Share keys securely with team members

2. **Use different keys for different environments**
   - Development: Simple key for testing
   - Production: Complex, randomly generated key

3. **Rotate keys periodically**
   - Change API key every few months
   - Update all clients when rotating

4. **Generate secure keys**
   ```bash
   # PowerShell
   -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 40 | ForEach-Object {[char]$_})
   
   # Python
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

## ❌ Common Errors

### Error: Missing API Key (401)
```json
{
  "detail": "Missing API Key. Please provide 'X-API-Key' header."
}
```
**Solution**: Add `X-API-Key` header to your request

### Error: Invalid API Key (403)
```json
{
  "detail": "Invalid API Key"
}
```
**Solution**: Check that your API key matches the one in `.env`

## 📚 Protected Endpoints

Currently protected:
- `POST /api/v1/auth/login` - Requires API key

Not protected (public):
- `GET /` - Service info
- `GET /health` - Health check
- `GET /hello` - Hello endpoint

To protect other endpoints, add `api_key: str = Depends(verify_api_key)` to the route function.

## 🔧 Troubleshooting

1. **Service returning 500 error**
   - Check Docker logs: `docker-compose logs auth_service`
   - Rebuild container: `docker-compose build --no-cache auth_service`

2. **API key not working after restart**
   - Verify `.env` file is mounted in docker-compose.yml
   - Check if `ENABLE_API_KEY=true` in `.env`

3. **Need to bypass API key temporarily**
   - Set `ENABLE_API_KEY=false` in `.env`
   - Restart the service
