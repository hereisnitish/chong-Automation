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
    email_folder_id = models.CharField(max_length=255)
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



