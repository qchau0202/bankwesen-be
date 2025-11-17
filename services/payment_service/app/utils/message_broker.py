
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class MessageBroker:
    def __init__(self):
        self.enabled = True
    
    async def publish(self, event_type: str, payload: Dict[str, Any]) -> bool:
        if not self.enabled:
            return False
        
        try:
            message = {
                "event_type": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "payload": payload
            }
            
            logger.info(f"[MESSAGE BROKER] Publishing event: {event_type}")
            logger.debug(f"[MESSAGE BROKER] Payload: {payload}")
            
            return True
            
        except Exception as e:
            logger.error(f"[MESSAGE BROKER] Error publishing event: {e}")
            return False
    
    async def subscribe(self, event_type: str, callback):
        logger.info(f"[MESSAGE BROKER] Subscribed to: {event_type}")
        pass


# Singleton instance
broker = MessageBroker()

async def notify_payment_created(payment_id: str, customer_id: str, tuition_id: str, amount: float):
    await broker.publish("payment.created", {
        "payment_id": payment_id,
        "customer_id": customer_id,
        "tuition_id": tuition_id,
        "amount": amount,
        "status": "pending"
    })


async def notify_payment_completed(payment_id: str, customer_id: str, tuition_id: str, amount: float):
    await broker.publish("payment.completed", {
        "payment_id": payment_id,
        "customer_id": customer_id,
        "tuition_id": tuition_id,
        "amount": amount,
        "status": "completed"
    })


async def notify_payment_cancelled(payment_id: str, customer_id: str, tuition_id: str):
    await broker.publish("payment.cancelled", {
        "payment_id": payment_id,
        "customer_id": customer_id,
        "tuition_id": tuition_id,
        "status": "cancelled"
    })


async def notify_payment_failed(payment_id: str, customer_id: str, tuition_id: str, reason: str):
    await broker.publish("payment.failed", {
        "payment_id": payment_id,
        "customer_id": customer_id,
        "tuition_id": tuition_id,
        "status": "failed",
        "reason": reason
    })
