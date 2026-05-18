from django.db import models
from django.conf import settings
from datetime import timedelta
from django.utils import timezone
import secrets

class MobileToken(models.Model):
    """Token for mobile app authentication"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    def is_valid(self):
        return timezone.now() <= self.expires_at
    
    @classmethod
    def create_token(cls, user, expiry_hours=24):
        token = secrets.token_hex(32)
        expires_at = timezone.now() + timedelta(hours=expiry_hours)
        return cls.objects.create(user=user, token=token, expires_at=expires_at)
    
    def __str__(self):
        return f"{self.user.username} - {self.token[:20]}..."