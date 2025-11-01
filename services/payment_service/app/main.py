from fastapi import FastAPI
import httpx
import os

app = FastAPI(title="Payment Service")

@app.get("/")
async def root():
    return {"service": "Payment Service", "status": "running"}

@app.get("/hello")
async def hello():
    return {"message": "Hello from Payment Service!"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/call-auth")
async def call_auth():
    auth_url = os.getenv("AUTH_SERVICE_URL", "http://auth_service:8001")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{auth_url}/hello", timeout=5.0)
            return {"payment_service": "called Auth service", "auth_response": response.json()}
        except Exception as e:
            return {"payment_service": "error", "error": str(e)}
