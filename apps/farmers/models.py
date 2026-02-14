from django.db import models 
from django.conf import settings 
from django.core.validators import MinValueValidator, RegexValidator 
from django.utils import timezone 
 
class FarmerProfile(models.Model): 
    user = models.OneToOneField( 
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='farmer_profile', 
        null=True, 
        blank=True 
    ) 
 
    first_name = models.CharField(max_length=100) 
    last_name = models.CharField(max_length=100) 
    national_id = models.CharField(max_length=20, unique=True, help_text="National ID/Passport number") 
 
    phone_regex = RegexValidator( 
        regex=r'\+?254?\d{9,12}$', 
        message="Phone number must be in format: '+254XXXXXXXXX' or '07XXXXXXXX'" 
    ) 
    phone_number = models.CharField( 
        validators=[phone_regex], 
        max_length=15, 
        unique=True, 
        help_text="Required for SMS notifications" 
    ) 
    alt_phone_number = models.CharField(max_length=15, blank=True, null=True) 
 
    region = models.CharField(max_length=100, choices=[ 
        ('central', 'Central'), 
        ('eastern', 'Eastern'), 
        ('western', 'Western'), 
        ('rift_valley', 'Rift Valley'), 
        ('coast', 'Coast'), 
        ('nairobi', 'Nairobi'), 
        ('north_eastern', 'North Eastern'), 
        ('nyanza', 'Nyanza'), 
    ]) 
    district = models.CharField(max_length=100) 
    village = models.CharField(max_length=100) 
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True) 
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True) 
 
    farm_name = models.CharField(max_length=200) 
    farm_size_acres = models.DecimalField( 
        max_digits=8, 
        decimal_places=2, 
        validators=[MinValueValidator(0.1)] 
    ) 
    coffee_varieties = models.TextField( 
        help_text="List varieties grown (e.g., SL28, Ruiru 11, Batian, K7)" 
    ) 
    years_farming = models.IntegerField(default=1) 
 
    sms_notifications = models.BooleanField( 
        default=True, 
        help_text="Receive SMS for deliveries and payments" 
    ) 
    sms_language = models.CharField( 
        max_length=10, 
        choices=[('en', 'English'), ('sw', 'Kiswahili')], 
        default='en' 
    ) 
 
    bank_name = models.CharField(max_length=100, blank=True) 
    bank_account = models.CharField(max_length=50, blank=True) 
    bank_branch = models.CharField(max_length=100, blank=True) 
    mobile_money_number = models.CharField(max_length=15, blank=True, help_text="M-Pesa/Airtel Money number") 
    mobile_money_provider = models.CharField( 
        max_length=20, 
        choices=[ 
            ('mpesa', 'M-Pesa'), 
            ('airtel', 'Airtel Money'), 
            ('telkom', 'Telkom T-Cash'), 
        ], 
        blank=True 
    ) 
 
    registered_by = models.ForeignKey( 
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='registered_farmers' 
    ) 
    registration_date = models.DateTimeField(auto_now_add=True) 
    updated_at = models.DateTimeField(auto_now=True) 
    is_active = models.BooleanField(default=True) 
 
    class Meta: 
        app_label = 'farmers' 
        ordering = ['-registration_date'] 
        indexes = [ 
            models.Index(fields=['phone_number']), 
            models.Index(fields=['national_id']), 
            models.Index(fields=['region', 'district']), 
        ] 
 
    def __str__(self): 
        return f"{self.first_name} {self.last_name} - {self.farm_name}" 
 
    def full_name(self): 
        return f"{self.first_name} {self.last_name}" 
