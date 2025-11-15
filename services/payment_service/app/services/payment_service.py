from datetime import datetime, timedelta
from typing import Optional, Dict, Any, TYPE_CHECKING
import uuid
import httpx
import logging
from fastapi import HTTPException, status

if TYPE_CHECKING:
    from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.payment import PaymentModel
from app.schemas.payment_schema import PaymentCreateRequest
from app.core.config import settings

logger = logging.getLogger(__name__)


class PaymentService:
    """Service for handling payment operations"""
    
    MAX_OTP_ATTEMPTS = 3
    PAYMENT_EXPIRY_MINUTES = 60
    
    def __init__(self, db: Any):
        self.db = db
        self.payments_collection = db["payments"]
    
    async def create_payment(self, request: PaymentCreateRequest, auth_token: str, user_email: Optional[str] = None) -> PaymentModel:
        """
        Create a new payment with idempotency key to prevent duplicates.
        Lock the payment to allow only one payment per tuition per user.
        
        Args:
            request: Payment creation request
            auth_token: JWT token for authenticating internal service calls
            
        Returns:
            Created payment
            
        Raises:
            HTTPException: If payment already exists or tuition not found
        """
        try:
            # Generate idempotency key from customer and tuition
            idempotency_key = f"{request.customerId}_{request.tuitionId}_{datetime.utcnow().timestamp()}"
            
            # Check if ANY payment already exists for this tuition (pending or completed) - regardless of customer
            # This prevents multiple users from paying for the same tuition simultaneously
            existing_payment = await self.payments_collection.find_one({
                "tuitionId": request.tuitionId,
                "status": {"$in": ["pending", "completed"]}
            })
            
            if existing_payment:
                # If the payment belongs to a different customer, inform them
                if existing_payment.get("customerId") != request.customerId:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"This tuition is already being paid by another user (Payment ID: {existing_payment.get('paymentId')}). Please wait or contact support."
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Payment already exists for this tuition. Please complete or cancel the existing payment first."
                    )
            
            # Fetch tuition information from tuition service
            tuition_data = await self._get_tuition_info(request.tuitionId, auth_token)
            
            if not tuition_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Tuition with ID {request.tuitionId} not found"
                )
            
            # Check if tuition is already paid
            if tuition_data.get("status") == "paid":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This tuition has already been paid"
                )
            
            # Generate payment ID
            payment_id = f"PAY{int(datetime.utcnow().timestamp())}{str(uuid.uuid4())[:6]}"
            
            # Create payment document
            payment = PaymentModel(
                paymentId=payment_id,
                customerId=request.customerId,
                tuitionId=request.tuitionId,
                idempotency_key=idempotency_key,
                amount=tuition_data.get("tuition_amount", 0),
                status="pending",
                otp_attempts=0,
                is_locked=False,
                created_at=datetime.utcnow(),
                expired_at=datetime.utcnow() + timedelta(minutes=self.PAYMENT_EXPIRY_MINUTES)
            )
            
            # Insert into database
            payment_dict = payment.model_dump(by_alias=True, exclude={"id"})
            try:
                result = await self.payments_collection.insert_one(payment_dict)
            except Exception as db_error:
                # Handle MongoDB duplicate key error (race condition)
                if "duplicate key error" in str(db_error).lower():
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="This tuition is already being paid by another user. Please try again later."
                    )
                raise
            
            # Notify other services and automatically request OTP
            await self._notify_payment_created(payment, user_email)
            
            logger.info(f"Payment created: {payment_id} for tuition {request.tuitionId}")
            
            return payment
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating payment: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create payment: {str(e)}"
            )
    
    async def get_payment(self, payment_id: str) -> Optional[PaymentModel]:
        """
        Get payment by ID
        
        Args:
            payment_id: Payment ID
            
        Returns:
            Payment or None if not found
        """
        payment_dict = await self.payments_collection.find_one({"paymentId": payment_id})
        if payment_dict:
            return PaymentModel(**payment_dict)
        return None
    
    async def request_otp(self, payment_id: str, email: str) -> Dict[str, Any]:
        """
        Request OTP for payment verification
        
        Args:
            payment_id: Payment ID
            email: Customer email
            
        Returns:
            OTP request response
            
        Raises:
            HTTPException: If payment not found, locked, or expired
        """
        payment = await self.get_payment(payment_id)
        
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        if payment.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot request OTP for payment with status: {payment.status}"
            )
        
        if payment.is_locked:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Payment is locked due to multiple failed attempts. Please create a new payment."
            )
        
        # Check if payment expired
        if payment.expired_at and datetime.utcnow() > payment.expired_at:
            await self._update_payment_status(payment_id, "failed")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment has expired"
            )
        
        # Call OTP service to generate and send OTP
        try:
            otp_url = f"{settings.OTP_SERVICE_URL}/api/otp/request"
            otp_payload = {
                "payment_id": payment_id,
                "tuition_id": payment.tuitionId,
                "user_id": payment.customerId,
                "email": email,
                "amount": payment.amount
            }
            logger.info(f"Requesting OTP from {otp_url}")
            logger.info(f"OTP payload: payment_id={payment_id}, email={email}, amount={payment.amount}")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    otp_url,
                    json=otp_payload,
                    headers={"x-api-key": settings.API_KEY},
                    timeout=10.0
                )
                
                if response.status_code != 201:
                    logger.error(f"OTP service returned status {response.status_code}: {response.text}")
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Failed to request OTP: {response.text}"
                    )
                
                logger.info(f"OTP requested successfully for payment {payment_id}")
                return response.json()
        
        except httpx.TimeoutException as e:
            logger.error(f"OTP service timeout: {e}")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="OTP service timeout"
            )
        except httpx.RequestError as e:
            logger.error(f"Error calling OTP service: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"OTP service unavailable: {str(e)}"
            )
    
    async def verify_otp(self, payment_id: str, otp_code: str) -> PaymentModel:
        """
        Verify OTP and complete payment
        
        Args:
            payment_id: Payment ID
            otp_code: OTP code to verify
            
        Returns:
            Updated payment
            
        Raises:
            HTTPException: If verification fails
        """
        payment = await self.get_payment(payment_id)
        
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        if payment.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot verify OTP for payment with status: {payment.status}"
            )
        
        if payment.is_locked:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Payment is locked due to multiple failed attempts"
            )
        
        # Increment OTP attempts
        new_attempts = payment.otp_attempts + 1
        await self.payments_collection.update_one(
            {"paymentId": payment_id},
            {"$set": {"otp_attempts": new_attempts}}
        )
        
        # Verify OTP with OTP service
        try:
            logger.info(f"Verifying OTP for payment {payment_id}, attempt {new_attempts}/{self.MAX_OTP_ATTEMPTS}")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.OTP_SERVICE_URL}/api/otp/verify",
                    json={
                        "payment_id": payment_id,
                        "otp_code": otp_code
                    },
                    headers={"x-api-key": settings.API_KEY},
                    timeout=10.0
                )
                
                logger.info(f"OTP service response: status={response.status_code}, body={response.text}")
                
                if response.status_code == 200:
                    # OTP verified successfully, process payment
                    result = response.json()
                    
                    if not result.get("success"):
                        # OTP verification failed but service returned 200
                        error_msg = result.get("message", "OTP verification failed")
                        attempts_remaining = result.get("attempts_remaining", 0)
                        is_locked = result.get("locked", False)
                        
                        logger.warning(f"OTP verification failed: {error_msg}, attempts_remaining={attempts_remaining}")
                        
                        if is_locked or new_attempts >= self.MAX_OTP_ATTEMPTS:
                            # Lock payment
                            await self.payments_collection.update_one(
                                {"paymentId": payment_id},
                                {"$set": {
                                    "is_locked": True,
                                    "status": "cancelled"
                                }}
                            )
                            raise HTTPException(
                                status_code=status.HTTP_423_LOCKED,
                                detail="Maximum OTP attempts reached. Payment has been cancelled."
                            )
                        
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"{error_msg}. Attempts remaining: {self.MAX_OTP_ATTEMPTS - new_attempts}"
                        )
                    
                    # Process the transaction in try-catch block
                    try:
                        # 1. Deduct customer balance first
                        await self._deduct_customer_balance(payment.customerId, payment.amount)
                        
                        # 2. Update tuition status to paid
                        await self._update_tuition_status(payment.tuitionId)
                        
                        # 3. Update payment status to completed in a single atomic operation
                        await self.payments_collection.update_one(
                            {"paymentId": payment_id},
                            {"$set": {
                                "status": "completed",
                                "otp_attempts": new_attempts,
                                "is_locked": False,
                                "expired_at": None,
                                "completed_at": datetime.utcnow()
                            }}
                        )
                        
                        logger.info(f"Payment {payment_id} completed successfully - Amount {payment.amount} deducted from customer {payment.customerId}")
                        
                    except Exception as e:
                        logger.error(f"Error processing transaction: {e}")
                        await self._update_payment_status(payment_id, "failed")
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Transaction failed: {str(e)}"
                        )
                    
                    # Get updated payment
                    updated_payment = await self.get_payment(payment_id)
                    if not updated_payment:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to retrieve updated payment"
                        )
                    return updated_payment
                    
                elif response.status_code == 400:
                    # OTP verification failed
                    if new_attempts >= self.MAX_OTP_ATTEMPTS:
                        # Lock payment after max attempts
                        await self.payments_collection.update_one(
                            {"paymentId": payment_id},
                            {"$set": {
                                "is_locked": True,
                                "status": "cancelled"
                            }}
                        )
                        raise HTTPException(
                            status_code=status.HTTP_423_LOCKED,
                            detail="Maximum OTP attempts reached. Payment has been cancelled."
                        )
                    
                    error_detail = response.json().get("detail", "Invalid OTP")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"{error_detail}. Attempts remaining: {self.MAX_OTP_ATTEMPTS - new_attempts}"
                    )
                else:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"OTP verification failed: {response.text}"
                    )
        
        except HTTPException as e:
            raise e
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="OTP service timeout"
            )
        except httpx.RequestError as e:
            logger.error(f"Error calling OTP service: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OTP service unavailable"
            )
        except Exception as e:
            logger.error(f"Unexpected error in verify_otp: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to verify OTP"
            )
    
    async def cancel_payment(self, payment_id: str) -> bool:
        """
        Cancel a payment
        
        Args:
            payment_id: Payment ID
            
        Returns:
            True if cancelled successfully
            
        Raises:
            HTTPException: If payment not found or cannot be cancelled
        """
        payment = await self.get_payment(payment_id)
        
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        if payment.status not in ["pending"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel payment with status: {payment.status}"
            )
        
        # Update payment status
        await self._update_payment_status(payment_id, "cancelled")
        logger.info(f"Payment {payment_id} cancelled")
        
        return True
    
    async def _update_payment_status(self, payment_id: str, status: str):
        """Update payment status"""
        await self.payments_collection.update_one(
            {"paymentId": payment_id},
            {"$set": {"status": status}}
        )
    
    async def _get_tuition_info(self, tuition_id: str, auth_token: str) -> Optional[Dict[str, Any]]:
        """Get tuition information from tuition service"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.TUITION_SERVICE_URL}/api/tuition/record/{tuition_id}",
                    headers={
                        "x-api-key": settings.API_KEY,
                        "Authorization": f"Bearer {auth_token}"
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    logger.warning(f"Tuition {tuition_id} not found")
                else:
                    logger.error(f"Error fetching tuition: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error fetching tuition info: {e}")
            return None
    
    async def _deduct_customer_balance(self, customer_id: str, amount: float):
        """Deduct amount from customer's balance via auth service"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.AUTH_SERVICE_URL}/api/v1/auth/deduct-balance",
                    json={
                        "customer_id": customer_id,
                        "amount": amount
                    },
                    headers={"x-api-key": settings.API_KEY},
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    error_detail = response.json().get("detail", response.text)
                    raise Exception(f"Failed to deduct customer balance: {error_detail}")
                    
                logger.info(f"Deducted {amount} from customer {customer_id}")
        except Exception as e:
            logger.error(f"Error deducting customer balance: {e}")
            raise
    
    async def _update_tuition_status(self, tuition_id: str):
        """Update tuition status to paid"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{settings.TUITION_SERVICE_URL}/api/tuition/{tuition_id}/status",
                    json={"status": "paid"},
                    headers={"x-api-key": settings.API_KEY},
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    raise Exception(f"Failed to update tuition status: {response.text}")
                    
                logger.info(f"Updated tuition {tuition_id} to paid status")
        except Exception as e:
            logger.error(f"Error updating tuition status: {e}")
            raise
    
    async def _notify_payment_created(self, payment: PaymentModel, user_email: Optional[str] = None):
        """
        Notify other services when payment is created and automatically request OTP.
        
        This method automatically calls the OTP service to generate and send the OTP email
        immediately after payment creation, so the user receives the email without needing
        to make a separate API call.
        
        NOTE: In production, this should be done via message broker (RabbitMQ, Kafka, etc.)
        where OTP service subscribes to "payment.created" events.
        """
        try:
            logger.info(f"[AUTO-OTP] Payment created: {payment.paymentId}")
            
            if not user_email:
                logger.warning(f"[AUTO-OTP] No email provided, skipping automatic OTP generation")
                return
            
            logger.info(f"[AUTO-OTP] Automatically requesting OTP for {user_email}...")
            
            # Directly call OTP service to generate and send OTP
            try:
                otp_url = f"{settings.OTP_SERVICE_URL}/api/otp/request"
                otp_payload = {
                    "payment_id": payment.paymentId,
                    "tuition_id": payment.tuitionId,
                    "user_id": payment.customerId,
                    "email": user_email,
                    "amount": payment.amount
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        otp_url,
                        json=otp_payload,
                        headers={"x-api-key": settings.API_KEY},
                        timeout=10.0
                    )
                    
                    if response.status_code == 201:
                        logger.info(f"[AUTO-OTP] ✅ OTP generated and email sent automatically to {user_email}")
                        logger.info(f"[AUTO-OTP] User can now verify OTP for payment {payment.paymentId}")
                    else:
                        logger.warning(f"[AUTO-OTP] ⚠️ Failed to auto-generate OTP: {response.status_code} - {response.text}")
                        logger.info(f"[AUTO-OTP] User can manually request OTP via POST /api/payment/{payment.paymentId}/otp")
                        
            except httpx.RequestError as e:
                logger.error(f"[AUTO-OTP] ❌ Error calling OTP service: {e}")
                logger.info(f"[AUTO-OTP] User can manually request OTP via POST /api/payment/{payment.paymentId}/otp")
            
            # Future implementation with message broker:
            # await broker.publish("payment.created", {
            #     "payment_id": payment.paymentId,
            #     "customer_id": payment.customerId,
            #     "tuition_id": payment.tuitionId,
            #     "amount": payment.amount,
            #     "email": user_email
            # })
            # Then OTP service subscribes to "payment.created" events and auto-generates OTP
            
        except Exception as e:
            # Don't fail payment creation if notification fails
            logger.error(f"[AUTO-OTP] Error in auto OTP generation: {e}")
            logger.info(f"[AUTO-OTP] User can manually request OTP via POST /api/payment/{payment.paymentId}/otp")
