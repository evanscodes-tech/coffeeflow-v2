import random
import string
from django.utils import timezone
from datetime import timedelta

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def is_otp_valid(otp_created_at):
    """Check if OTP is still valid (5 minutes)"""
    if not otp_created_at:
        return False
    expiry_time = otp_created_at + timedelta(minutes=5)
    return timezone.now() <= expiry_time