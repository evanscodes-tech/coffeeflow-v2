from django.db import models 
from django.conf import settings 
from django.core.validators import MinValueValidator 
from django.utils import timezone 
from farmers.models import FarmerProfile 
 
class CoffeeBatch(models.Model): 
    BATCH_STATUS = [ 
        ('pending', 'Pending Payment'), 
        ('paid', 'Paid'), 
        ('disputed', 'Disputed'), 
    ] 
 
    QUALITY_GRADES = [ 
        ('specialty', 'Specialty (85-100)'), 
        ('premium', 'Premium (80-84)'), 
        ('standard', 'Standard (70-79)'), 
        ('commercial', 'Commercial (below 70)'), 
    ] 
 
    farmer = models.ForeignKey( 
        FarmerProfile, 
        on_delete=models.CASCADE, 
        related_name='coffee_batches' 
    ) 
 
    batch_code = models.CharField(max_length=50, unique=True, blank=True) 
 
    delivery_date = models.DateField(default=timezone.now) 
    cherry_weight_kg = models.DecimalField( 
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0.1)], 
        help_text="Weight of coffee cherry in kilograms" 
    ) 
 
    dry_weight_kg = models.DecimalField( 
        max_digits=10, 
        decimal_places=2, 
        editable=False, 
        help_text="5kg cherry = 1kg dry coffee (auto-calculated)" 
    ) 
 
    quality_grade = models.CharField( 
        max_length=20, 
        choices=QUALITY_GRADES, 
        default='standard' 
    ) 
    cupping_score = models.IntegerField(null=True, blank=True, help_text="Score out of 100") 
 
    price_per_kg = models.DecimalField( 
        max_digits=10, 
        decimal_places=2, 
        default=120.00, 
        help_text="Price per kg of dry coffee in KES" 
    ) 
    total_amount = models.DecimalField( 
        max_digits=12, 
        decimal_places=2, 
        editable=False, 
        help_text="Auto-calculated: (cherry_weight_kg / 5) * price_per_kg" 
    ) 
    payment_status = models.CharField( 
        max_length=20, 
        choices=BATCH_STATUS, 
        default='pending' 
    ) 
 
    recorded_by = models.ForeignKey( 
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='recorded_batches' 
    ) 
 
    sms_sent = models.BooleanField(default=False) 
    sms_sent_at = models.DateTimeField(null=True, blank=True) 
    sms_status = models.CharField(max_length=50, blank=True, help_text="SMS delivery status") 
 
    created_at = models.DateTimeField(auto_now_add=True) 
    updated_at = models.DateTimeField(auto_now=True) 
 
    class Meta: 
        app_label = 'deliveries' 
        ordering = ['-delivery_date', '-created_at'] 
        indexes = [ 
            models.Index(fields=['farmer', 'delivery_date']), 
            models.Index(fields=['payment_status']), 
            models.Index(fields=['batch_code']), 
        ] 
 
    def __str__(self): 
        return f"{self.batch_code} - {self.farmer.full_name()} - {self.cherry_weight_kg}kg" 
 
    def save(self, *args, **kwargs): 
        if not self.batch_code: 
            import uuid 
            self.batch_code = f"CF-{timezone.now().strftime('%Y%m')}-{str(uuid.uuid4())[:6].upper()}" 
 
        self.dry_weight_kg = self.cherry_weight_kg / 5 
        self.total_amount = self.dry_weight_kg * self.price_per_kg 
        super().save(*args, **kwargs) 
 
        if not self.sms_sent and self.farmer.sms_notifications: 
            self.send_sms_notification() 
 
    def send_sms_notification(self): 
        self.sms_sent = True 
        self.sms_sent_at = timezone.now() 
        self.sms_status = "SMS would be sent here" 
        self.save() 
        print(f"?? SMS would be sent to {self.farmer.phone_number}: {self.cherry_weight_kg}kg delivered") 
