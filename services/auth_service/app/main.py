from fastapi import FastAPI
import httpx
import os

app = FastAPI(title="Auth Service")

@app.get("/")
async def root():
    return {"service": "Auth Service", "status": "running"}

@app.get("/hello")
async def hello():
    return {"message": "Hello from Auth Service!"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/call-otp")
async def call_otp():
    otp_url = os.getenv("OTP_SERVICE_URL", "http://otp_service:8002")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{otp_url}/hello", timeout=5.0)
            return {"auth_service": "called OTP service", "otp_response": response.json()}
        except Exception as e:
            return {"auth_service": "error", "error": str(e)}
