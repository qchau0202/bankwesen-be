from fastapi import FastAPI
import httpx
import os

app = FastAPI(title="Tuition Service")

@app.get("/")
async def root():
    return {"service": "Tuition Service", "status": "running"}

@app.get("/hello")
async def hello():
    return {"message": "Hello from Tuition Service!"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/call-payment")
async def call_payment():
    payment_url = os.getenv("PAYMENT_SERVICE_URL", "http://payment_service:8003")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{payment_url}/hello", timeout=5.0)
            return {"tuition_service": "called Payment service", "payment_response": response.json()}
        except Exception as e:
            return {"tuition_service": "error", "error": str(e)}
