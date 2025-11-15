"""
Debug script to test OTP email flow with detailed logging
"""
import asyncio
import httpx
import sys

# Configuration
API_KEY = "bankwesen-api-key-2024-secure-change-in-production"

async def test_full_flow():
    """Test the complete flow with detailed output"""
    
    print("\n" + "="*70)
    print("🔍 TESTING OTP EMAIL FLOW - DEBUG MODE")
    print("="*70 + "\n")
    
    # Step 1: Login
    print("📝 Step 1: Login to get authentication token")
    print("-" * 70)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8001/api/v1/auth/login",
                json={
                    "username": "longduong",
                    "password": "password123"
                },
                headers={"X-API-Key": API_KEY},
                timeout=10.0
            )
            
            if response.status_code != 200:
                print(f"❌ Login failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            data = response.json()
            token = data["access_token"]
            email = data["user_info"].get("email")
            customer_id = data["user_info"].get("customerId")
            
            print(f"✅ Login successful")
            print(f"   Customer ID: {customer_id}")
            print(f"   Email: {email}")
            print(f"   Token: {token[:20]}...")
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False
    
    # Step 2: Create Payment
    print("\n📝 Step 2: Create a payment")
    print("-" * 70)
    
    try:
        payment_data = {
            "customerId": customer_id,
            "tuitionId": "TU2024110001",
            "idempotency_key": f"test-debug-{asyncio.get_event_loop().time()}",
            "amount": 15000000.0
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8003/api/payment/",
                json=payment_data,
                headers={
                    "X-API-Key": API_KEY,
                    "Authorization": f"Bearer {token}"
                },
                timeout=10.0
            )
            
            if response.status_code == 409:
                print("⚠️  Payment already exists (409), trying to get existing payment...")
                # For debugging, we'll create a new one with different key
                payment_data["idempotency_key"] = f"test-debug-new-{asyncio.get_event_loop().time()}"
                response = await client.post(
                    "http://localhost:8003/api/payment/",
                    json=payment_data,
                    headers={
                        "X-API-Key": API_KEY,
                        "Authorization": f"Bearer {token}"
                    },
                    timeout=10.0
                )
            
            if response.status_code != 201:
                print(f"❌ Payment creation failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            payment = response.json()
            payment_id = payment["paymentId"]
            
            print(f"✅ Payment created")
            print(f"   Payment ID: {payment_id}")
            print(f"   Amount: ${payment['amount']}")
            print(f"   Status: {payment['status']}")
            
    except Exception as e:
        print(f"❌ Payment creation error: {e}")
        return False
    
    # Step 3: Request OTP
    print("\n📝 Step 3: Request OTP (this should send email)")
    print("-" * 70)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://localhost:8003/api/payment/{payment_id}/otp",
                headers={
                    "X-API-Key": API_KEY,
                    "Authorization": f"Bearer {token}"
                },
                timeout=15.0
            )
            
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}\n")
            
            if response.status_code != 200:
                print(f"❌ OTP request failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            otp_data = response.json()
            print(f"✅ OTP request successful")
            print(f"   Message: {otp_data.get('message')}")
            print(f"   Expires in: {otp_data.get('expires_in')} seconds")
            print(f"   Attempts remaining: {otp_data.get('attempts_remaining')}")
            
    except httpx.TimeoutException:
        print("❌ Request timeout - service took too long to respond")
        return False
    except Exception as e:
        print(f"❌ OTP request error: {e}")
        return False
    
    # Step 4: Check logs
    print("\n📝 Step 4: Checking service logs")
    print("-" * 70)
    print("\n✅ Test completed! Now checking logs...\n")
    
    return True

async def check_service_health():
    """Check if all services are healthy"""
    print("\n🏥 Checking service health...")
    print("-" * 70)
    
    services = {
        "Payment Service": "http://localhost:8003/",
        "OTP Service": "http://localhost:8002/",
        "Notification Service": "http://localhost:8004/",
    }
    
    all_healthy = True
    async with httpx.AsyncClient() as client:
        for name, url in services.items():
            try:
                response = await client.get(url, timeout=5.0)
                if response.status_code == 200:
                    print(f"✅ {name}: Online")
                else:
                    print(f"⚠️  {name}: Returned {response.status_code}")
                    all_healthy = False
            except Exception as e:
                print(f"❌ {name}: Offline - {e}")
                all_healthy = False
    
    print()
    return all_healthy

async def main():
    print("\n" + "="*70)
    print("🚀 OTP EMAIL FLOW DEBUG TEST")
    print("="*70)
    
    # Check services first
    if not await check_service_health():
        print("\n❌ Some services are not healthy. Please check docker-compose ps")
        return
    
    # Run the test
    success = await test_full_flow()
    
    if success:
        print("\n" + "="*70)
        print("✅ TEST FLOW COMPLETED SUCCESSFULLY")
        print("="*70)
        print("\n📧 Check your email inbox for the OTP!")
        print("\n📋 To see detailed logs, run these commands:")
        print("   docker-compose logs --tail=30 payment_service")
        print("   docker-compose logs --tail=30 otp_service")
        print("   docker-compose logs --tail=30 notification_service")
    else:
        print("\n" + "="*70)
        print("❌ TEST FAILED - Check the errors above")
        print("="*70)
        print("\n📋 Check logs for details:")
        print("   docker-compose logs --tail=50 payment_service")
        print("   docker-compose logs --tail=50 otp_service")
        print("   docker-compose logs --tail=50 notification_service")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
