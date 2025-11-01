from fastapi import FastAPI
import httpx
import os

app = FastAPI(title="Notification Service")

@app.get("/")
async def root():
    return {"service": "Notification Service", "status": "running"}

@app.get("/hello")
async def hello():
    return {"message": "Hello from Notification Service!"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/call-tuition")
async def call_tuition():
    tuition_url = os.getenv("TUITION_SERVICE_URL", "http://tuition_service:8005")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{tuition_url}/hello", timeout=5.0)
            return {"notification_service": "called Tuition service", "tuition_response": response.json()}
        except Exception as e:
            return {"notification_service": "error", "error": str(e)}
