from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os

app = FastAPI(
    title="API Gateway",
    description="Central gateway for all microservices",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs from environment variables
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth_service:8001")
OTP_SERVICE_URL = os.getenv("OTP_SERVICE_URL", "http://otp_service:8002")
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://payment_service:8003")
NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification_service:8004")
TUITION_SERVICE_URL = os.getenv("TUITION_SERVICE_URL", "http://tuition_service:8005")


@app.get("/")
async def root():
    """Root endpoint - Gateway Hello World"""
    return {
        "message": "Hello from API Gateway!",
        "service": "gateway",
        "port": 8000
    }


@app.get("/hello")
async def hello():
    """Simple hello endpoint"""
    return {"message": "Hello World from Gateway!"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "gateway"}


@app.get("/call-all")
async def call_all_services():
    """Test endpoint that calls all services"""
    results = {}
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        services = {
            "auth": f"{AUTH_SERVICE_URL}/hello",
            "otp": f"{OTP_SERVICE_URL}/hello",
            "payment": f"{PAYMENT_SERVICE_URL}/hello",
            "notification": f"{NOTIFICATION_SERVICE_URL}/hello",
            "tuition": f"{TUITION_SERVICE_URL}/hello"
        }
        
        for service_name, url in services.items():
            try:
                response = await client.get(url)
                results[service_name] = response.json()
            except Exception as e:
                results[service_name] = {"error": str(e)}
    
    return {
        "gateway": "Hello from Gateway!",
        "services_called": results
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
