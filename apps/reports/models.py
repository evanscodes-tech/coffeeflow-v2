from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.conf import settings

class ReportTemplate(models.Model):
    """Saved report configurations"""
    REPORT_TYPES = [
        ('delivery_summary', 'Delivery Summary'),
        ('farmer_performance', 'Farmer Performance'),
        ('payment_analysis', 'Payment Analysis'),
        ('harvest_forecast', 'Harvest Forecast'),
        ('quality_analysis', 'Quality Analysis'),
    ]
    
    FORMAT_CHOICES = [
        ('chart', 'Chart'),
        ('table', 'Table'),
        ('both', 'Both'),
    ]
    
    name = models.CharField(max_length=100)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    description = models.TextField(blank=True)
    
    # Date range settings
    date_range = models.CharField(max_length=20, default='last_30_days')
    custom_start_date = models.DateField(null=True, blank=True)
    custom_end_date = models.DateField(null=True, blank=True)
    
    # Chart settings
    chart_type = models.CharField(max_length=20, default='bar', 
                                  choices=[('bar', 'Bar'), ('line', 'Line'), 
                                           ('pie', 'Pie'), ('area', 'Area')])
    chart_format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='both')
    
    # Filters (stored as JSON)
    filters = models.JSONField(default=dict, blank=True)
    
    # Group by options
    group_by = models.CharField(max_length=50, blank=True,
                                choices=[('farmer', 'Farmer'), ('month', 'Month'),
                                         ('week', 'Week'), ('quality', 'Quality Grade'),
                                         ('region', 'Region')])
    
    # Export settings
    auto_export = models.BooleanField(default=False)
    export_format = models.CharField(max_length=10, default='csv',
                                     choices=[('csv', 'CSV'), ('excel', 'Excel'),
                                              ('pdf', 'PDF')])
    
    # Schedule (for automated reports)
    scheduled = models.BooleanField(default=False)
    schedule_frequency = models.CharField(max_length=20, blank=True,
                                         choices=[('daily', 'Daily'), ('weekly', 'Weekly'),
                                                  ('monthly', 'Monthly')])
    
    # Metadata
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"

class ReportExport(models.Model):
    """Stored generated reports"""
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, related_name='exports')
    file = models.FileField(upload_to='reports/')
    format = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"{self.template.name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

class DashboardWidget(models.Model):
    """Customizable dashboard widgets"""
    WIDGET_TYPES = [
        ('chart', 'Chart'),
        ('metric', 'Metric'),
        ('table', 'Table'),
        ('alert', 'Alert'),
    ]
    
    title = models.CharField(max_length=100)
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES)
    
    # Position on dashboard
    row = models.IntegerField(default=1)
    column = models.IntegerField(default=1)
    width = models.IntegerField(default=6)  # Bootstrap column width (1-12)
    height = models.CharField(max_length=20, default='medium',
                             choices=[('small', 'Small'), ('medium', 'Medium'),
                                      ('large', 'Large')])
    
    # Data source
    report_template = models.ForeignKey(ReportTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    metric_field = models.CharField(max_length=50, blank=True)
    
    # Display settings
    color_scheme = models.CharField(max_length=20, default='default')
    show_title = models.BooleanField(default=True)
    refresh_interval = models.IntegerField(default=0, help_text="Refresh interval in seconds (0 for no refresh)")
    
    # User preferences
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dashboard_widgets')
    is_visible = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['row', 'column']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"