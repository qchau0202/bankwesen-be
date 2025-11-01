from fastapi import FastAPI
import httpx
import os

app = FastAPI(title="OTP Service")

@app.get("/")
async def root():
    return {"service": "OTP Service", "status": "running"}

@app.get("/hello")
async def hello():
    return {"message": "Hello from OTP Service!"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/call-notification")
async def call_notification():
    notification_url = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification_service:8004")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{notification_url}/hello", timeout=5.0)
            return {"otp_service": "called Notification service", "notification_response": response.json()}
        except Exception as e:
            return {"otp_service": "error", "error": str(e)}
