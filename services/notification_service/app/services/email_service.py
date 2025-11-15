import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending emails"""
    
    @staticmethod
    async def send_email(to_email: str, subject: str, html_content: str) -> bool:
        """
        Send email using SMTP
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content of the email
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL or settings.SMTP_USER}>"
            message["To"] = to_email
            message["Subject"] = subject
            
            # Attach HTML content
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Send email
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                start_tls=True
            )
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    @staticmethod
    def generate_otp_email(otp_code: str, expires_in: int, payment_id: str, amount: float) -> str:
        """Generate HTML content for OTP email"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f9f9f9;
                }}
                .header {{
                    background-color: #4CAF50;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background-color: white;
                    padding: 30px;
                    border-radius: 0 0 5px 5px;
                }}
                .otp-code {{
                    font-size: 32px;
                    font-weight: bold;
                    color: #4CAF50;
                    text-align: center;
                    padding: 20px;
                    background-color: #f0f0f0;
                    border-radius: 5px;
                    letter-spacing: 8px;
                    margin: 20px 0;
                }}
                .info {{
                    background-color: #e8f5e9;
                    padding: 15px;
                    border-left: 4px solid #4CAF50;
                    margin: 20px 0;
                }}
                .warning {{
                    background-color: #fff3cd;
                    padding: 15px;
                    border-left: 4px solid #ffc107;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    color: #666;
                    font-size: 12px;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Payment Verification</h1>
                </div>
                <div class="content">
                    <h2>Your OTP Code</h2>
                    <p>Please use the following code to verify your payment:</p>
                    
                    <div class="otp-code">{otp_code}</div>
                    
                    <div class="info">
                        <strong>Payment Details:</strong><br>
                        Payment ID: {payment_id}<br>
                        Amount: ${amount:,.2f}
                    </div>
                    
                    <div class="warning">
                        <strong>⚠️ Important:</strong><br>
                        • This code will expire in <strong>{expires_in} seconds</strong><br>
                        • You have <strong>3 attempts</strong> to enter the correct code<br>
                        • Do not share this code with anyone
                    </div>
                    
                    <p>If you didn't request this code, please ignore this email or contact our support team.</p>
                </div>
                <div class="footer">
                    <p>This is an automated email from Bankwesen Banking System.</p>
                    <p>Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    @staticmethod
    def generate_transaction_email(
        recipient_name: str,
        payer_name: str,
        transaction_id: str,
        payment_id: str,
        amount: float,
        timestamp: str,
        tuition_info: dict = None,
        is_payer: bool = True
    ) -> str:
        """Generate HTML content for transaction confirmation email"""
        
        if is_payer:
            title = "Payment Confirmation"
            message = f"Your payment has been processed successfully!"
        else:
            title = "Payment Received"
            message = f"A payment has been made for your tuition fee by {payer_name}!"
        
        tuition_section = ""
        if tuition_info:
            tuition_section = f"""
            <div class="info">
                <strong>Tuition Information:</strong><br>
                Student: {tuition_info.get('student_name', 'N/A')}<br>
                Course: {tuition_info.get('course', 'N/A')}<br>
                Semester: {tuition_info.get('semester', 'N/A')}
            </div>
            """
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f9f9f9;
                }}
                .header {{
                    background-color: #2196F3;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background-color: white;
                    padding: 30px;
                    border-radius: 0 0 5px 5px;
                }}
                .success-icon {{
                    text-align: center;
                    font-size: 64px;
                    color: #4CAF50;
                    margin: 20px 0;
                }}
                .info {{
                    background-color: #e3f2fd;
                    padding: 15px;
                    border-left: 4px solid #2196F3;
                    margin: 20px 0;
                }}
                .amount {{
                    font-size: 36px;
                    font-weight: bold;
                    color: #4CAF50;
                    text-align: center;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    color: #666;
                    font-size: 12px;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{title}</h1>
                </div>
                <div class="content">
                    <div class="success-icon">✓</div>
                    <h2>Transaction Successful</h2>
                    <p>{message}</p>
                    
                    <div class="amount">${amount:,.2f}</div>
                    
                    <div class="info">
                        <strong>Transaction Details:</strong><br>
                        Transaction ID: {transaction_id}<br>
                        Payment ID: {payment_id}<br>
                        Date & Time: {timestamp}<br>
                        Payer: {payer_name}<br>
                        Recipient: {recipient_name}
                    </div>
                    
                    {tuition_section}
                    
                    <p>Thank you for using Bankwesen Banking System!</p>
                    <p>If you have any questions about this transaction, please contact our support team with the transaction ID above.</p>
                </div>
                <div class="footer">
                    <p>This is an automated email from Bankwesen Banking System.</p>
                    <p>Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    async def send_otp_email(
        self,
        email: str,
        otp_code: str,
        expires_in: int,
        payment_id: str,
        amount: float
    ) -> bool:
        """Send OTP email to user"""
        subject = f"Your OTP Code - {otp_code}"
        html_content = self.generate_otp_email(otp_code, expires_in, payment_id, amount)
        return await self.send_email(email, subject, html_content)
    
    async def send_transaction_email(
        self,
        recipient_email: str,
        payer_email: str,
        recipient_name: str,
        payer_name: str,
        transaction_id: str,
        payment_id: str,
        amount: float,
        timestamp: str,
        tuition_info: dict = None
    ) -> tuple[bool, bool]:
        """
        Send transaction confirmation emails to both payer and recipient
        
        Returns:
            Tuple of (payer_email_sent, recipient_email_sent)
        """
        # Send to payer
        payer_html = self.generate_transaction_email(
            recipient_name, payer_name, transaction_id, payment_id,
            amount, timestamp, tuition_info, is_payer=True
        )
        payer_sent = await self.send_email(
            payer_email,
            "Payment Confirmation - Transaction Successful",
            payer_html
        )
        
        # Send to recipient (if different from payer)
        recipient_sent = True
        if payer_email != recipient_email:
            recipient_html = self.generate_transaction_email(
                recipient_name, payer_name, transaction_id, payment_id,
                amount, timestamp, tuition_info, is_payer=False
            )
            recipient_sent = await self.send_email(
                recipient_email,
                "Payment Received - Tuition Fee Paid",
                recipient_html
            )
        
        return payer_sent, recipient_sent
