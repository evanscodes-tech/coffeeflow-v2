from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', _('Admin')
        STAFF = 'staff', _('Staff')
        FARMER = 'farmer', _('Farmer')
    
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.FARMER
    )
    phone_number = models.CharField(max_length=15, unique=True, blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    
    # OTP (One-Time Password) fields for two-factor authentication
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    otp_verified = models.BooleanField(default=False)
    
    # Explicitly define groups and user_permissions with unique related_name
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        related_name='customuser_set',
        related_query_name='customuser',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        related_name='customuser_set',
        related_query_name='customuser',
    )
    
    class Meta:
        app_label = 'accounts'
        db_table = 'accounts_customuser'
    
    def __str__(self):
        return f"{self.username} ({self.role})"
    
    def is_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser
    
    def is_staff_user(self):
        return self.role == self.Role.STAFF or self.is_admin()
    
    def is_farmer(self):
        return self.role == self.Role.FARMER