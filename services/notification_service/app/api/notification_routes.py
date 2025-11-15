from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.notification_schema import (
    EmailOTPRequest,
    EmailTransactionRequest,
    EmailResponse
)
from app.services.email_service import EmailService
from app.core.security import verify_api_key
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notification", tags=["Notification"], dependencies=[Depends(verify_api_key)])

email_service = EmailService()

@router.post("/email-otp", response_model=EmailResponse, status_code=status.HTTP_200_OK)
async def send_otp_email(request: EmailOTPRequest):
    """
    Send OTP email to user
    
    This endpoint is called by the OTP service after generating an OTP code
    """
    try:
        logger.info(f"Received request to send OTP email to {request.email} for payment {request.payment_id}")
        
        success = await email_service.send_otp_email(
            email=request.email,
            otp_code=request.otp_code,
            expires_in=request.expires_in,
            payment_id=request.payment_id,
            amount=request.amount
        )
        
        if success:
            return EmailResponse(
                success=True,
                message="OTP email sent successfully",
                email_sent_to=[request.email]
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send OTP email"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending OTP email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send OTP email: {str(e)}"
        )

@router.post("/email-transaction", response_model=EmailResponse, status_code=status.HTTP_200_OK)
async def send_transaction_email(request: EmailTransactionRequest):
    """
    Send transaction confirmation email to both payer and recipient
    
    This endpoint is called after a successful payment transaction.
    Sends confirmation email to:
    1. The person who paid (payer)
    2. The person whose tuition was paid (recipient) - if different from payer
    """
    try:
        payer_sent, recipient_sent = await email_service.send_transaction_email(
            recipient_email=request.recipient_email,
            payer_email=request.payer_email,
            recipient_name=request.recipient_name,
            payer_name=request.payer_name,
            transaction_id=request.transaction_id,
            payment_id=request.payment_id,
            amount=request.amount,
            timestamp=request.timestamp,
            tuition_info=request.tuition_info
        )
        
        emails_sent = []
        if payer_sent:
            emails_sent.append(request.payer_email)
        if recipient_sent and request.payer_email != request.recipient_email:
            emails_sent.append(request.recipient_email)
        
        if payer_sent or recipient_sent:
            return EmailResponse(
                success=True,
                message=f"Transaction confirmation email(s) sent to {len(emails_sent)} recipient(s)",
                email_sent_to=emails_sent
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send transaction confirmation emails"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending transaction email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send transaction email: {str(e)}"
        )

@router.get("/test-email")
async def test_email_configuration():
    """
    Test email configuration
    
    This endpoint can be used to verify that the email service is configured correctly
    """
    try:
        from app.core.config import settings
        
        return {
            "smtp_configured": bool(settings.SMTP_HOST and settings.SMTP_PASSWORD),
            "smtp_host": settings.SMTP_HOST,
            "smtp_port": settings.SMTP_PORT,
            "smtp_user": settings.SMTP_USER,
            "from_name": settings.SMTP_FROM_NAME
        }
    except Exception as e:
        logger.error(f"Error testing email configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test email configuration: {str(e)}"
        )
