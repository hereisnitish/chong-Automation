from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    phone_number = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'phone_number']

    def __str__(self):
        return self.email


class UserData(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='user_data'
    )
    company_name = models.CharField(max_length=255, blank=True, null=True)
    number_of_trucks = models.PositiveIntegerField(default=0)
    mc_number = models.CharField(max_length=50, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.company_name or 'No Company'}"


class Dashboard(models.Model):
    TYPE_CHOICES = [
        ('whatsapp', 'WhatsApp Message'),
        ('gmail', 'Gmail'),
        ('sms', 'SMS'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dashboards')
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    created_date = models.DateTimeField(default=timezone.now)
    google_drive_link = models.URLField(max_length=500, blank=True, null=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    
    class Meta:
        ordering = ['-created_date']
    
    def __str__(self):
        return f"{self.type} - {self.email} - {self.created_date.strftime('%Y-%m-%d')}"


class EmailFolder(models.Model):
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    company_name_folder_id = models.CharField(max_length=255)
    company_name_mc_number = models.CharField(max_length=255, blank=True, null=True)
    year_folder_id = models.CharField(max_length=255)
    month_folder_id = models.CharField(max_length=255)
    date_folder_id = models.CharField(max_length=255)
    folder_year = models.IntegerField(default=2025)
    folder_month = models.IntegerField(default=1)
    folder_date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    
    
    def __str__(self):
        return f"{self.email} - {self.folder_date}"


class LogEntry(models.Model):
    LEVEL_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='log_entries', null=True, blank=True)
    event = models.CharField(max_length=100)
    message = models.TextField(blank=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='info')
    related_model = models.CharField(max_length=100, blank=True, null=True)
    related_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.level.upper()}] {self.event} ({self.created_at.strftime('%Y-%m-%d %H:%M:%S')})"


class Lead(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMMUNICATED', 'Communicated'),
        ('COMPLETED', 'Completed'),
    ]

    HELP_NEEDED_CHOICES = [
        ('compliance', 'Compliance & Permits'),
        ('bookkeeping', 'Bookkeeping & Taxes'),
        ('growth', 'Business growth'),
        ('all', 'Everything'), 
    ]

    full_name = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    mc_number = models.CharField(max_length=50, blank=True, null=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    truck_count = models.CharField(max_length=50, blank=True, null=True)
    
    help_needed = models.CharField(
        max_length=50, 
        choices=HELP_NEEDED_CHOICES,
        default='all',
        help_text="Area where assistance is required"
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Lead"
        verbose_name_plural = "Leads"

    def __str__(self):
        return f"{self.full_name} - {self.company_name or 'No Company'} - {self.status}"