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
    
    async def create_payment(self, request: PaymentCreateRequest, auth_token: str, customer_id: str, user_email: Optional[str] = None) -> PaymentModel:
        """
        Create a new payment with idempotency key to prevent duplicates.
        Lock the payment to allow only one payment per tuition per user.
        
        Args:
            request: Payment creation request with tuition IDs
            auth_token: JWT token for authenticating internal service calls
            customer_id: Customer ID extracted from JWT token
            user_email: User email extracted from JWT token
            
        Returns:
            Created payment
            
        Raises:
            HTTPException: If payment already exists or tuition not found
        """
        try:
            # Handle tuitionIds input - convert to list
            tuition_ids = []
            if isinstance(request.tuitionIds, str):
                if request.tuitionIds.lower() == "all":
                    # Determine which student's tuitions to fetch
                    # If studentId is provided, use it; otherwise use customer_id (paying for self)
                    target_student_id = request.studentId if request.studentId else customer_id
                    
                    # Fetch all unpaid tuitions for the target student
                    tuition_ids = await self._get_all_unpaid_tuitions(target_student_id, auth_token)
                    if not tuition_ids:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"No unpaid tuitions found for student {target_student_id}"
                        )
                    logger.info(f"Customer {customer_id} paying all tuitions for student {target_student_id}: {tuition_ids}")
                else:
                    tuition_ids = [request.tuitionIds]
            else:
                tuition_ids = request.tuitionIds
            
            # Validate we have at least one tuition
            if not tuition_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="At least one tuition ID must be provided"
                )
            
            # Generate idempotency key from customer and tuition IDs
            tuition_ids_str = "_".join(sorted(tuition_ids))
            idempotency_key = f"{customer_id}_{tuition_ids_str}_{datetime.utcnow().timestamp()}"
            
            # Check if ANY payment already exists for these tuitions (pending or completed)
            existing_payment = await self.payments_collection.find_one({
                "tuitionIds": {"$in": tuition_ids},
                "status": {"$in": ["pending", "completed"]}
            })
            
            if existing_payment:
                # If the payment belongs to a different customer, inform them
                if existing_payment.get("customerId") != customer_id:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"One or more tuitions are already being paid by another user (Payment ID: {existing_payment.get('paymentId')}). Please wait or contact support."
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Payment already exists for one or more of these tuitions. Please complete or cancel the existing payment first."
                    )
            
            # Fetch tuition information for all tuitions and calculate total amount
            total_amount = 0.0
            tuition_data_list = []
            
            for tuition_id in tuition_ids:
                tuition_data = await self._get_tuition_info(tuition_id, auth_token)
                
                if not tuition_data:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Tuition with ID {tuition_id} not found"
                    )
                
                # Check if tuition is already paid
                if tuition_data.get("status") == "paid":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Tuition {tuition_id} has already been paid"
                    )
                
                tuition_data_list.append(tuition_data)
                total_amount += tuition_data.get("tuition_amount", 0)
            
            # Generate payment ID
            payment_id = f"PAY{int(datetime.utcnow().timestamp())}{str(uuid.uuid4())[:6]}"
            
            # Create payment document with multiple tuition IDs
            payment = PaymentModel(
                paymentId=payment_id,
                customerId=customer_id,
                tuitionIds=tuition_ids,
                idempotency_key=idempotency_key,
                amount=total_amount,
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
            logger.info(f"Attempting to send OTP to email: {user_email}")
            await self._notify_payment_created(payment, user_email)
            
            logger.info(f"Payment created: {payment_id} for tuitions {tuition_ids}")
            
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
                "tuition_ids": payment.tuitionIds,  # Send all tuition IDs
                "user_id": payment.customerId,
                "email": email,
                "amount": payment.amount
            }
            logger.info(f"Requesting OTP from {otp_url}")
            logger.info(f"OTP payload: payment_id={payment_id}, email={email}, amount={payment.amount}, tuition_ids={payment.tuitionIds}")
            
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
    
    async def verify_otp(self, payment_id: str, otp_code: str, auth_token: str) -> PaymentModel:
        """
        Verify OTP and complete payment
        
        Args:
            payment_id: Payment ID
            otp_code: OTP code to verify
            auth_token: JWT token for authenticating internal service calls
            
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
                        
                        # 2. Update all tuition statuses to paid
                        for tuition_id in payment.tuitionIds:
                            await self._update_tuition_status(tuition_id)
                        
                        # 3. Update payment status to completed in a single atomic operation
                        completed_at = datetime.utcnow()
                        await self.payments_collection.update_one(
                            {"paymentId": payment_id},
                            {"$set": {
                                "status": "completed",
                                "otp_attempts": new_attempts,
                                "is_locked": False,
                                "expired_at": None,
                                "completed_at": completed_at
                            }}
                        )
                        
                        logger.info(f"Payment {payment_id} completed successfully - Amount {payment.amount} deducted from customer {payment.customerId}")
                        
                        # 4. Send transaction completion emails to customer and recipient
                        try:
                            await self._send_transaction_completion_email(payment, completed_at, auth_token)
                        except Exception as e:
                            # Don't fail the payment if email sending fails
                            logger.warning(f"⚠️ Failed to send transaction completion email: {e}")
                        
                        # 5. Publish payment completion event via Redis message broker
                        try:
                            from app.broker.redis_broker import publish_event
                            await publish_event(
                                channel="payment.events",
                                event_type="payment.completed",
                                data={
                                    "payment_id": payment_id,
                                    "customer_id": payment.customerId,
                                    "tuition_ids": payment.tuitionIds,
                                    "amount": payment.amount,
                                    "completed_at": completed_at.isoformat()
                                }
                            )
                        except Exception as e:
                            # Don't fail the payment if event publishing fails
                            logger.warning(f"⚠️ Failed to publish payment completion event: {e}")
                        
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
    
    async def _get_all_unpaid_tuitions(self, student_id: str, auth_token: str) -> list:
        """
        Get all unpaid tuition IDs for a student from tuition service.
        
        Args:
            student_id: Student/Customer ID
            auth_token: JWT token for authentication
            
        Returns:
            List of unpaid tuition IDs
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.TUITION_SERVICE_URL}/api/tuition/{student_id}",
                    headers={
                        "x-api-key": settings.API_KEY,
                        "Authorization": f"Bearer {auth_token}"
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Filter only unpaid tuitions
                    tuitions = data.get("tuitions", [])
                    unpaid_ids = [t["tuitionId"] for t in tuitions if t.get("status") == "debt"]
                    logger.info(f"Found {len(unpaid_ids)} unpaid tuitions for student {student_id}")
                    return unpaid_ids
                elif response.status_code == 404:
                    logger.warning(f"No tuitions found for student {student_id}")
                    return []
                else:
                    logger.error(f"Error fetching student tuitions: {response.status_code} - {response.text}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching all unpaid tuitions: {e}")
            return []
    
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
        """Deduct amount from customer's balance directly from auth_db"""
        try:
            from app.db.mongodb import auth_database
            
            if auth_database is None:
                raise Exception("Auth database connection is not initialized")
            
            users_collection = auth_database["users"]
            
            logger.info(f"🔍 Looking for customer with customerId: {customer_id}")
            
            # Find the user by customerId field (not _id)
            user = await users_collection.find_one({"customerId": customer_id})
            
            if not user:
                # Try to find any user to debug the field name
                sample_user = await users_collection.find_one({})
                logger.error(f"🔍 Customer not found. Sample user structure: {sample_user}")
                logger.error(f"🔍 Searched for customerId: {customer_id}")
                raise Exception(f"Customer {customer_id} not found")
            
            logger.info(f"🔍 Found customer: {user.get('customerId')} with balance: {user.get('balance', 0)}")
            
            current_balance = user.get("balance", 0)
            if current_balance < amount:
                raise Exception(f"Insufficient balance. Current: {current_balance}, Required: {amount}")
            
            # Deduct balance atomically
            new_balance = current_balance - amount
            result = await users_collection.update_one(
                {"customerId": customer_id},
                {
                    "$set": {
                        "balance": new_balance,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count == 0:
                raise Exception(f"Failed to update balance for customer {customer_id}")
            
            logger.info(f"✅ Deducted {amount} from customer {customer_id}. New balance: {new_balance}")
        except Exception as e:
            logger.error(f"❌ Error deducting customer balance: {e}")
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
    
    async def _send_transaction_completion_email(self, payment: PaymentModel, completed_at: datetime, auth_token: str):
        """Send transaction completion email to customer and recipient via notification service"""
        try:
            # Get customer and tuition details
            from app.db.mongodb import auth_database
            
            if auth_database is None:
                logger.error("Auth database connection is not initialized")
                return
            
            users_collection = auth_database["users"]
            
            # Get payer (customer) details
            payer = await users_collection.find_one({"customerId": payment.customerId})
            if not payer:
                logger.error(f"Cannot send email: Payer {payment.customerId} not found")
                return
            
            payer_email = payer.get("email")
            payer_name = payer.get("full_name", payment.customerId)
            
            if not payer_email:
                logger.warning(f"Payer {payment.customerId} has no email address")
                return
            
            # Get all tuition details for email
            async with httpx.AsyncClient() as client:
                # Fetch all tuition records
                tuition_details = []
                for tuition_id in payment.tuitionIds:
                    tuition_response = await client.get(
                        f"{settings.TUITION_SERVICE_URL}/api/tuition/record/{tuition_id}",
                        headers={
                            "x-api-key": settings.API_KEY,
                            "Authorization": f"Bearer {auth_token}"
                        },
                        timeout=10.0
                    )
                    
                    if tuition_response.status_code == 200:
                        tuition_details.append(tuition_response.json())
                    else:
                        logger.warning(f"Failed to get tuition {tuition_id}: {tuition_response.text}")
                
                if not tuition_details:
                    logger.error(f"Failed to get any tuition details")
                    return
                
                # Use first tuition for student info (all tuitions belong to same student)
                first_tuition = tuition_details[0]
                recipient_id = first_tuition.get("studentId")
                
                # Check if customer is paying for themselves
                is_self_payment = (payment.customerId == recipient_id)
                
                # Get student email from tuition table (NOT from users table)
                recipient_email = first_tuition.get("studentEmail")
                recipient_name = first_tuition.get("studentName", recipient_id)
                
                if not recipient_email:
                    logger.error(f"No email found in tuition data for student {recipient_id}")
                    raise Exception(f"Student email not found in tuition record")
                
                if is_self_payment:
                    logger.info(f"Customer {payment.customerId} paid for their own tuitions - will send to customer email ({payer_email}) and student email ({recipient_email})")
                else:
                    logger.info(f"Customer {payment.customerId} paid for student {recipient_id}'s tuitions - will send to customer email ({payer_email}) and student email ({recipient_email})")
                
                # Prepare tuition details for email
                tuition_list = []
                for tuition in tuition_details:
                    tuition_list.append({
                        "tuition_id": tuition.get("tuitionId"),
                        "amount": tuition.get("tuition_amount", 0),
                        "academic_year": tuition.get("academic_year", "N/A"),
                        "semester": tuition.get("semester", "N/A"),
                        "description": f"Tuition Fee - {tuition.get('semester', 'N/A')}"
                    })
                
                # Send email via notification service
                notification_payload = {
                    "recipient_email": recipient_email,
                    "payer_email": payer_email,
                    "recipient_name": recipient_name,
                    "payer_name": payer_name,
                    "transaction_id": str(payment.paymentId),
                    "payment_id": payment.paymentId,
                    "amount": payment.amount,
                    "timestamp": completed_at.isoformat(),
                    "is_self_payment": is_self_payment,
                    "tuition_info": {
                        "student_id": recipient_id,
                        "tuitions": tuition_list
                    }
                }
                
                logger.info(f"📧 Sending notification payload: {notification_payload}")
                
                email_response = await client.post(
                    f"{settings.NOTIFICATION_SERVICE_URL}/api/notification/email-transaction",
                    json=notification_payload,
                    headers={"x-api-key": settings.API_KEY},
                    timeout=10.0
                )
                
                logger.info(f"📧 Notification response: {email_response.status_code} - {email_response.text}")
                
                if email_response.status_code == 200:
                    if is_self_payment:
                        logger.info(f"✅ Transaction completion email sent to {payer_email}")
                    else:
                        logger.info(f"✅ Transaction completion emails sent to payer ({payer_email}) and recipient ({recipient_email})")
                else:
                    logger.error(f"Failed to send transaction emails: {email_response.text}")
                    
        except Exception as e:
            logger.error(f"Error sending transaction completion email: {e}")
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
            logger.info(f"[AUTO-OTP] Customer ID: {payment.customerId}, Email: {user_email}")
            
            if not user_email:
                logger.error(f"[AUTO-OTP] ❌ No email provided for customer {payment.customerId}. Cannot send OTP automatically.")
                logger.info(f"[AUTO-OTP] User must manually request OTP via POST /api/payment/{payment.paymentId}/otp")
                return
            
            logger.info(f"[AUTO-OTP] Automatically requesting OTP for {user_email}...")
            
            # Directly call OTP service to generate and send OTP
            try:
                otp_url = f"{settings.OTP_SERVICE_URL}/api/otp/request"
                logger.info(f"[AUTO-OTP] OTP Service URL: {otp_url}")
                
                otp_payload = {
                    "payment_id": payment.paymentId,
                    "tuition_ids": payment.tuitionIds,
                    "user_id": payment.customerId,
                    "email": user_email,
                    "amount": payment.amount
                }
                logger.info(f"[AUTO-OTP] OTP Request Payload: {otp_payload}")
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        otp_url,
                        json=otp_payload,
                        headers={"x-api-key": settings.API_KEY},
                        timeout=10.0
                    )
                    
                    logger.info(f"[AUTO-OTP] OTP Service Response Status: {response.status_code}")
                    
                    if response.status_code == 201:
                        logger.info(f"[AUTO-OTP] ✅ OTP generated and email sent successfully to {user_email}")
                        logger.info(f"[AUTO-OTP] User can now verify OTP for payment {payment.paymentId}")
                    else:
                        logger.error(f"[AUTO-OTP] ⚠️ Failed to auto-generate OTP: {response.status_code}")
                        logger.error(f"[AUTO-OTP] Response: {response.text}")
                        logger.info(f"[AUTO-OTP] User can manually request OTP via POST /api/payment/{payment.paymentId}/otp")
                        
            except httpx.TimeoutException as e:
                logger.error(f"[AUTO-OTP] ❌ OTP service timeout: {e}")
                logger.info(f"[AUTO-OTP] User can manually request OTP via POST /api/payment/{payment.paymentId}/otp")
            except httpx.RequestError as e:
                logger.error(f"[AUTO-OTP] ❌ Error calling OTP service: {e}")
                logger.error(f"[AUTO-OTP] OTP Service URL attempted: {otp_url}")
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
