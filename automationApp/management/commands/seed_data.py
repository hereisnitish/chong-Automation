# core/management/commands/seed_data.py
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from faker import Faker
import random
import uuid

from automationApp.models import UserData, Dashboard, EmailFolder, LogEntry  # adjust import if your app name != core

User = get_user_model()
fake = Faker()


class Command(BaseCommand):
    help = "Seed database with fake data (users, userdata, dashboards, emailfolders, logentries)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--count', type=int, default=200, help='Number of users to create (and associated records)'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        count = options['count']
        created_users = 0

        TYPE_CHOICES = [choice[0] for choice in Dashboard.TYPE_CHOICES]
        LEVEL_CHOICES = [choice[0] for choice in LogEntry.LEVEL_CHOICES]

        for i in range(count):
            # construct unique email and phone
            email = f"{fake.user_name()}{i}@example.com"
            username = f"user{i}_{fake.user_name()[:8]}"
            phone = f"9{random.randint(100000000, 999999999)}"  # 10-digit-ish

            # create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password="password123",  # change later if needed
                first_name=fake.first_name(),
                last_name=fake.last_name(),
            )
            # set phone_number if your custom user model requires it
            try:
                user.phone_number = phone
                user.save()
            except Exception:
                # If phone_number is required in User creation or different field name, ignore or adjust
                pass

            created_users += 1

            # create UserData (one-to-one)
            UserData.objects.create(
                user=user,
                company_name=fake.company(),
                number_of_trucks=random.randint(0, 200),
                mc_number=f"MC{random.randint(10000,99999)}",
                phone_number=phone,
            )

            # create several dashboard entries per user (1-5)
            for _ in range(random.randint(1, 5)):
                Dashboard.objects.create(
                    user=user,
                    email=email,
                    phone_number=phone,
                    created_date=fake.date_time_between(start_date='-2y', end_date='now', tzinfo=timezone.get_current_timezone()),
                    google_drive_link=fake.url(),
                    type=random.choice(TYPE_CHOICES),
                )

            # create one email folder per user
            folder_date = fake.date_between(start_date='-2y', end_date='today')
            EmailFolder.objects.create(
                email=email,
                phone_number=phone,
                email_folder_id=f"ef_{uuid.uuid4().hex[:12]}",
                year_folder_id=f"y_{folder_date.year}_{uuid.uuid4().hex[:6]}",
                month_folder_id=f"m_{folder_date.month}_{uuid.uuid4().hex[:6]}",
                date_folder_id=f"d_{folder_date.day}_{uuid.uuid4().hex[:6]}",
                folder_year=folder_date.year,
                folder_month=folder_date.month,
                folder_date=folder_date,
            )

            # create a few log entries
            for _ in range(random.randint(1, 4)):
                LogEntry.objects.create(
                    user=user,
                    event=random.choice(['import_email', 'upload_file', 'parse_error', 'login']),
                    message=fake.sentence(nb_words=12),
                    level=random.choice(LEVEL_CHOICES),
                    related_model=random.choice(['Dashboard', 'EmailFolder', 'UserData', 'None']),
                    related_id=str(random.randint(1, 1000)),
                    created_at=fake.date_time_between(start_date='-2y', end_date='now', tzinfo=timezone.get_current_timezone()),
                )

        self.stdout.write(self.style.SUCCESS(f"Created {created_users} users and associated fake data."))
