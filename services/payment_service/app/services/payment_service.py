from datetime import datetime, timedelta
from typing import Optional, Dict, Any, TYPE_CHECKING, List
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
    
    PAYMENT_EXPIRY_MINUTES = 60
    
    def __init__(self, db: Any):
        self.db = db
        self.payments_collection = db["payments"]
    
    async def createPaymentAsync(self, request: PaymentCreateRequest, auth_token: str, customer_id: str, user_email: Optional[str] = None) -> PaymentModel:
        try:
            target_student_id = request.studentId
            logger.info(f"CREATE PAYMENT REQUEST: Customer {customer_id} wants to pay for student {target_student_id}")
            
            tuition_ids, tuition_data_list = await self._getAllUnpaidTuitionsAsync(target_student_id, auth_token)
            
            if not tuition_ids:
                logger.warning(f"No unpaid tuitions found for student {target_student_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No unpaid tuitions found for student {target_student_id}"
                )
            
            logger.info(f"Customer {customer_id} paying all debt tuitions for student {target_student_id}: {tuition_ids}")
            
            tuition_ids_str = "_".join(sorted(tuition_ids))
            idempotency_key = f"{customer_id}_{tuition_ids_str}_{datetime.utcnow().timestamp()}"
            
            logger.info(f"Checking for existing payments with tuitionIds in: {tuition_ids}")
            existing_payment = await self.payments_collection.find_one({
                "tuitionIds": {"$in": tuition_ids},
                "status": {"$in": ["pending", "completed"]}
            })
            
            if existing_payment:
                logger.warning(f"Found existing payment: {existing_payment.get('paymentId')} with tuitionIds: {existing_payment.get('tuitionIds')} and status: {existing_payment.get('status')}")
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
            
            # Calculate total amount from the fetched tuition data
            total_amount = 0.0
            
            for tuition_data in tuition_data_list:
                if tuition_data.get("status") == "paid":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Tuition {tuition_data.get('tuitionId')} has already been paid"
                    )
                
                total_amount += tuition_data.get("tuition_amount", 0)
            
            payment_id = f"PAY{int(datetime.utcnow().timestamp())}{str(uuid.uuid4())[:6]}"
            
            payment = PaymentModel(
                paymentId=payment_id,
                customerId=customer_id,
                tuitionIds=tuition_ids,
                idempotency_key=idempotency_key,
                amount=total_amount,
                status="pending",
                created_at=datetime.utcnow()
            )
            
            payment_dict = payment.model_dump(by_alias=True, exclude={"id"})
            try:
                result = await self.payments_collection.insert_one(payment_dict)
            except Exception as db_error:
                if "duplicate key error" in str(db_error).lower():
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="This tuition is already being paid by another user. Please try again later."
                    )
                raise
            
            logger.info(f"Attempting to send OTP to email: {user_email}")
            otp_result = await self._notifyPaymentCreatedAsync(payment, user_email)
            
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
    
    async def getPaymentAsync(self, payment_id: str) -> Optional[PaymentModel]:
        payment_dict = await self.payments_collection.find_one({"paymentId": payment_id})
        if payment_dict:
            return PaymentModel(**payment_dict)
        return None

    async def getCustomerPaymentRecordsAsync(self, customer_id: str, auth_token: str) -> List[Dict[str, Any]]:
        try:
            cursor = self.payments_collection.find({"customerId": customer_id}).sort("created_at", -1)
            payments: List[PaymentModel] = [PaymentModel(**doc) async for doc in cursor]

            payment_records: List[Dict[str, Any]] = []
            for payment in payments:
                tuition_details = await self._fetchTuitionDetailsAsync(payment.tuitionIds, auth_token)
                payment_records.append(
                    {
                        "payment": payment,
                        "tuitions": tuition_details
                    }
                )

            return payment_records
        except Exception as e:
            logger.error(f"Error fetching payment records for customer {customer_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch payment records"
            )
    
    async def verifyOtpAsync(self, payment_id: str, otp_code: str, auth_token: str) -> Dict[str, Any]:
        payment = await self.getPaymentAsync(payment_id)
        
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
        
        # Verify OTP with OTP service
        try:
            logger.info(f"Verifying OTP for payment {payment_id}")
            
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
                    result = response.json()
                    
                    if not result.get("success"):
                        error_msg = result.get("message", "OTP verification failed")
                        
                        logger.warning(f"OTP verification failed: {error_msg}")
                        
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=error_msg
                        )
                    
                    # Process the transaction in try-catch block
                    try:
                        # 1. Deduct customer balance first
                        new_balance = await self._deductCustomerBalanceAsync(payment.customerId, payment.amount)
                        
                        # 2. Update all tuition statuses to paid
                        for tuition_id in payment.tuitionIds:
                            await self._updateTuitionStatusAsync(tuition_id)
                        
                        # 3. Update payment status to completed in a single atomic operation
                        completed_at = datetime.utcnow()
                        await self.payments_collection.update_one(
                            {"paymentId": payment_id},
                            {"$set": {
                                "status": "completed",
                                "completed_at": completed_at
                            }}
                        )
                        
                        logger.info(f"Payment {payment_id} completed successfully - Amount {payment.amount} deducted from customer {payment.customerId}")
                        
                        from app.core.security import create_access_token
                        from app.db.mongodb import auth_database
                        
                        users_collection = auth_database["users"]
                        user = await users_collection.find_one({"customerId": payment.customerId})
                        
                        new_access_token = None
                        if user:
                            # Append this paymentId to the user's payment_history
                            try:
                                await users_collection.update_one(
                                    {"customerId": payment.customerId},
                                    {"$push": {"payment_history": payment_id}}
                                )
                                logger.info(f"Appended payment {payment_id} to user {payment.customerId}'s payment_history")
                            except Exception as e:
                                logger.warning(f"Failed to append payment history for user {payment.customerId}: {e}")
                            token_data = {
                                "sub": user.get("username"),
                                "customerId": user.get("customerId"),
                                "username": user.get("username"),
                                "email": user.get("email"),
                                "balance": new_balance
                            }
                            
                            logger.info(f"Creating JWT token with data: {token_data}")
                            
                            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
                            new_access_token = create_access_token(
                                data=token_data,
                                expires_delta=access_token_expires
                            )
                            logger.info(f"Generated new JWT token with updated balance {new_balance} for customer {payment.customerId}")
                            
                            from app.core.security import decode_access_token
                            decoded = decode_access_token(new_access_token)
                            if decoded:
                                logger.info(f"Decoded JWT token balance: {decoded.get('balance')} (expected: {new_balance})")
                            else:
                                logger.error("Failed to decode newly created JWT token")
                        else:
                            logger.warning(f"Could not generate new token - user not found")
                        
                        try:
                            await self._sendTransactionCompletionEmailAsync(payment, completed_at, auth_token)
                        except Exception as e:
                            logger.warning(f"Failed to send transaction completion email: {e}")
                        
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
                            logger.warning(f"Failed to publish payment completion event: {e}")
                        
                    except Exception as e:
                        logger.error(f"Error processing transaction: {e}")
                        await self._updatePaymentStatusAsync(payment_id, "failed")
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Transaction failed: {str(e)}"
                        )
                    
                    # Get updated payment
                    updated_payment = await self.getPaymentAsync(payment_id)
                    if not updated_payment:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to retrieve updated payment"
                        )
                    
                    # Return payment with new token
                    return {
                        "payment": updated_payment,
                        "new_access_token": new_access_token,
                        "token_type": "bearer" if new_access_token else None,
                        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60 if new_access_token else None
                    }
                    
                elif response.status_code == 400:
                    # OTP verification failed
                    error_detail = response.json().get("detail", "Invalid OTP")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=error_detail
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
    
    async def cancelPaymentAsync(self, payment_id: str) -> bool:
        payment = await self.getPaymentAsync(payment_id)
        
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
        await self._updatePaymentStatusAsync(payment_id, "cancelled")
        logger.info(f"Payment {payment_id} cancelled")
        
        return True
    
    async def _updatePaymentStatusAsync(self, payment_id: str, status: str):
        await self.payments_collection.update_one(
            {"paymentId": payment_id},
            {"$set": {"status": status}}
        )
    
    async def _getAllUnpaidTuitionsAsync(self, student_id: str, auth_token: str) -> tuple[list, list]:
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
                    unpaid_tuitions = [t for t in tuitions if t.get("status") == "debt"]
                    unpaid_ids = [t["tuitionId"] for t in unpaid_tuitions]
                    logger.info(f"Found {len(unpaid_ids)} unpaid tuitions for student {student_id}: {unpaid_ids}")
                    return unpaid_ids, unpaid_tuitions
                elif response.status_code == 404:
                    logger.warning(f"No tuitions found for student {student_id}")
                    return [], []
                else:
                    logger.error(f"Error fetching student tuitions: {response.status_code} - {response.text}")
                    return [], []
        except Exception as e:
            logger.error(f"Error fetching all unpaid tuitions: {e}")
            return [], []
    
    async def _deductCustomerBalanceAsync(self, customer_id: str, amount: float) -> float:
        try:
            from app.db.mongodb import auth_database
            
            if auth_database is None:
                raise Exception("Auth database connection is not initialized")
            
            users_collection = auth_database["users"]
            
            logger.info(f"Looking for customer with customerId: {customer_id}")
            
            user = await users_collection.find_one({"customerId": customer_id})
            
            if not user:
                sample_user = await users_collection.find_one({})
                logger.error(f"Customer not found. Sample user structure: {sample_user}")
                logger.error(f"Searched for customerId: {customer_id}")
                raise Exception(f"Customer {customer_id} not found")
            
            logger.info(f"Found customer: {user.get('customerId')} with balance: {user.get('balance', 0)}")
            
            current_balance = user.get("balance", 0)
            if current_balance < amount:
                raise Exception(f"Insufficient balance. Current: {current_balance}, Required: {amount}")
            
            # Deduct balance atomically
            new_balance = current_balance - amount
            result = await users_collection.update_one(
                {"customerId": customer_id},
                {
                    "$set": {
                        "balance": new_balance
                    }
                }
            )
            
            if result.modified_count == 0:
                raise Exception(f"Failed to update balance for customer {customer_id}")
            
            logger.info(f"Deducted {amount} from customer {customer_id}. New balance: {new_balance}")
            return new_balance
        except Exception as e:
            logger.error(f"Error deducting customer balance: {e}")
            raise
    
    async def _updateTuitionStatusAsync(self, tuition_id: str):
        try:
            from app.db.mongodb import tuition_database
            
            if tuition_database is None:
                raise Exception("Tuition database connection is not initialized")
            
            tuitions_collection = tuition_database["tuitions"]
            
            # Update tuition status to paid (case-insensitive search)
            result = await tuitions_collection.update_one(
                {"tuitionId": {"$regex": f"^{tuition_id}$", "$options": "i"}},
                {
                    "$set": {
                        "status": "paid"
                    }
                }
            )
            
            if result.modified_count == 0:
                logger.warning(f"No tuition found with ID {tuition_id} to update")
            else:
                logger.info(f"Updated tuition {tuition_id} to paid status")
        except Exception as e:
            logger.error(f"Error updating tuition status: {e}")
            raise
    
    async def _sendTransactionCompletionEmailAsync(self, payment: PaymentModel, completed_at: datetime, auth_token: str):
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
            
            # Get tuition details from Tuition Service for each tuitionId
            tuition_details = []
            async with httpx.AsyncClient() as client:
                for tuition_id in payment.tuitionIds:
                    try:
                        tuition_resp = await client.get(
                            f"{settings.TUITION_SERVICE_URL}/api/tuition/record/{tuition_id}",
                            headers={
                                "x-api-key": settings.API_KEY,
                                "Authorization": f"Bearer {auth_token}"
                            },
                            timeout=10.0
                        )
                        if tuition_resp.status_code == 200:
                            tuition_details.append(tuition_resp.json())
                        else:
                            logger.warning(f"Tuition service returned {tuition_resp.status_code} for {tuition_id}: {tuition_resp.text}")
                    except Exception as e:
                        logger.warning(f"Failed to fetch tuition {tuition_id} from tuition service: {e}")
            
            if not tuition_details:
                logger.error(f"Failed to get any tuition details from database")
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
                "payment_id": payment.paymentId,
                "amount": payment.amount,
                "timestamp": completed_at.isoformat(),
                "is_self_payment": is_self_payment,
                "tuition_info": {
                    "student_id": recipient_id,
                    "tuitions": tuition_list
                }
            }
            
            logger.info(f"Sending notification payload: {notification_payload}")
            
            async with httpx.AsyncClient() as client:
                email_response = await client.post(
                    f"{settings.NOTIFICATION_SERVICE_URL}/api/notification/email-transaction",
                    json=notification_payload,
                    headers={"x-api-key": settings.API_KEY},
                    timeout=10.0
                )
                
                logger.info(f"Notification response: {email_response.status_code} - {email_response.text}")
                
                if email_response.status_code == 200:
                    if is_self_payment:
                        logger.info(f"Transaction completion email sent to {payer_email}")
                    else:
                        logger.info(f"Transaction completion emails sent to payer ({payer_email}) and recipient ({recipient_email})")
                else:
                    logger.error(f"Failed to send transaction emails: {email_response.text}")
                    
        except Exception as e:
            logger.error(f"Error sending transaction completion email: {e}")
            raise
    
    async def _notifyPaymentCreatedAsync(self, payment: PaymentModel, user_email: Optional[str] = None) -> Optional[Dict[str, Any]]:
        try:
            logger.info(f"[AUTO-OTP] Payment created: {payment.paymentId}")
            logger.info(f"[AUTO-OTP] Customer ID: {payment.customerId}, Email: {user_email}")
            
            if not user_email:
                logger.error(f"[AUTO-OTP] No email provided for customer {payment.customerId}. Cannot send OTP automatically.")
                logger.info(f"[AUTO-OTP] User must manually request OTP via POST /api/payment/{payment.paymentId}/otp")
                return None
            
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
                        logger.info(f"[AUTO-OTP] OTP generated and email sent successfully to {user_email}")
                        logger.info(f"[AUTO-OTP] User can now verify OTP for payment {payment.paymentId}")
                        otp_response = response.json()
                        return {
                            "success": True,
                            "expires_in": otp_response.get("expires_in", 60)
                        }
                    else:
                        logger.error(f"[AUTO-OTP] Failed to auto-generate OTP: {response.status_code}")
                        logger.error(f"[AUTO-OTP] Response: {response.text}")
                        logger.info(f"[AUTO-OTP] User can manually request OTP via POST /api/payment/{payment.paymentId}/otp")
                        return None
                        
            except httpx.TimeoutException as e:
                logger.error(f"[AUTO-OTP] OTP service timeout: {e}")
                logger.info(f"[AUTO-OTP] User can manually request OTP via POST /api/payment/{payment.paymentId}/otp")
                return None
            except httpx.RequestError as e:
                logger.error(f"[AUTO-OTP] Error calling OTP service: {e}")
                logger.error(f"[AUTO-OTP] OTP Service URL attempted: {otp_url}")
                logger.info(f"[AUTO-OTP] User can manually request OTP via POST /api/payment/{payment.paymentId}/otp")
                return None
            
        except Exception as e:
            # Don't fail payment creation if notification fails
            logger.error(f"[AUTO-OTP] Error in auto OTP generation: {e}")
            logger.info(f"[AUTO-OTP] User can manually request OTP via POST /api/payment/{payment.paymentId}/otp")
            return None

    async def _fetchTuitionDetailsAsync(self, tuition_ids: List[str], auth_token: str) -> List[Dict[str, Any]]:
        if not tuition_ids:
            return []

        tuition_details: List[Dict[str, Any]] = []
        try:
            async with httpx.AsyncClient() as client:
                for tuition_id in tuition_ids:
                    try:
                        response = await client.get(
                            f"{settings.TUITION_SERVICE_URL}/api/tuition/record/{tuition_id}",
                            headers={
                                "x-api-key": settings.API_KEY,
                                "Authorization": f"Bearer {auth_token}"
                            },
                            timeout=10.0
                        )
                        if response.status_code == 200:
                            tuition_details.append(response.json())
                        else:
                            logger.warning(
                                f"Failed to fetch tuition {tuition_id} for payment history "
                                f"(status={response.status_code}, body={response.text})"
                            )
                    except Exception as tuition_error:
                        logger.warning(f"Error fetching tuition {tuition_id}: {tuition_error}")

        except Exception as e:
            logger.error(f"Error fetching tuition details: {e}")

        return tuition_details
