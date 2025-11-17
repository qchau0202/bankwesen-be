import random
import string

def generate_otp(length: int = 6) -> str:
    """Generate a random OTP code with specified length"""
    return ''.join(random.choices(string.digits, k=length))

def generate_numeric_otp(length: int = 6) -> str:
    """Generate a numeric OTP code with specified length"""
    return ''.join(str(random.randint(0, 9)) for _ in range(length))