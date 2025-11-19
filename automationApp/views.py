from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from .models import User, Dashboard, EmailFolder, LogEntry
from django.db import IntegrityError,transaction
from django.db.models import Q
import requests
import json


from django.contrib.auth import get_user_model
from .models import UserData

User = get_user_model()

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        first_name = (request.POST.get('first_name') or '').strip()
        last_name = (request.POST.get('last_name') or '').strip()
        email = (request.POST.get('email') or '').strip().lower()
        username = (request.POST.get('username') or '').strip()
        phone_number = (request.POST.get('phone_number') or '').strip()
        password = request.POST.get('password') or ''
        password_confirm = request.POST.get('password_confirm') or ''

        company_name = (request.POST.get('company_name') or '').strip()
        mc_number_raw = (request.POST.get('mc_number') or '').strip()
        number_of_trucks_raw = (request.POST.get('number_of_trucks') or '').strip()

        # basic password check
        if password != password_confirm:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'signup.html')

        # normalize MC format to MC-XXXXXX (accepts with/without MC-, any whitespace)
        import re
        mc_digits = ''.join(re.findall(r'\d', mc_number_raw))
        mc_number = f"MC-{mc_digits}" if mc_digits else ''

        # parse trucks as non-negative int
        try:
            number_of_trucks = int(number_of_trucks_raw)
            if number_of_trucks < 0:
                number_of_trucks = 0
        except (TypeError, ValueError):
            number_of_trucks = 0

        # Create user + related userdata atomically
        try:
            with transaction.atomic():
                # since your User has USERNAME_FIELD='email', username can still be stored if you keep the field,
                # but auth will use email for login.
                user = User.objects.create_user(
                    username=username,     # keep if your model still has username
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    phone_number=phone_number,
                )

                # create the related UserData row
                UserData.objects.create(
                    user=user,
                    company_name=company_name or None,
                    mc_number=mc_number or None,
                    number_of_trucks=number_of_trucks,
                    phone_number=phone_number or None,  # optional mirror
                )

            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('dashboard')

        except IntegrityError:
            # likely unique email/phone/username clash
            messages.error(request, 'Email, username, or phone number already exists.')
            return render(request, 'signup.html')

    return render(request, 'signup.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is None:
            try:
                user_obj = User.objects.get(email=username)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username/email or password.')
    
    return render(request, 'login.html')


@login_required(login_url='login')
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')

@login_required(login_url='login')
def dashboard_view(request):
    is_admin = request.user.is_staff or request.user.is_superuser
    
    if is_admin:
        dashboard_qs = (
            Dashboard.objects
            .select_related('user')
            .order_by('-created_date')
        )
        email_folders_qs = EmailFolder.objects.all().order_by('-folder_date', '-created_at')
    else:
        dashboard_qs = (
            Dashboard.objects
            .filter(user=request.user)
            .select_related('user')
            .order_by('-created_date')
        )
        email_folders_qs = EmailFolder.objects.filter(
            Q(email=request.user.email) | Q(phone_number=request.user.phone_number)
        ).order_by('-folder_date', '-created_at')

    user_data = getattr(request.user, 'user_data', None)
    company_name = getattr(user_data, 'company_name', None)
    mc_number = getattr(user_data, 'mc_number', None)
    number_of_trucks = getattr(user_data, 'number_of_trucks', None)

    records = list(dashboard_qs)
    for r in records:
        if is_admin:
            r_user_data = getattr(r.user, 'user_data', None)
            r.company_name = getattr(r_user_data, 'company_name', None) if r_user_data else None
            r.mc_number = getattr(r_user_data, 'mc_number', None) if r_user_data else None
            r.number_of_trucks = getattr(r_user_data, 'number_of_trucks', None) if r_user_data else None
        else:
            r.company_name = company_name
            r.mc_number = mc_number
            r.number_of_trucks = number_of_trucks

    total_records = len(records)
    whatsapp_count = sum(1 for r in records if r.type == 'whatsapp')
    gmail_count = sum(1 for r in records if r.type == 'gmail')
    sms_count = sum(1 for r in records if r.type == 'sms')

    per_page = int(request.GET.get('per_page', 50))
    if per_page not in [10, 50, 100]:
        per_page = 50
    
    paginator = Paginator(records, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    if is_admin:
        years = Dashboard.objects.datetimes('created_date', 'year', order='DESC')
    else:
        years = Dashboard.objects.filter(user=request.user).datetimes('created_date', 'year', order='DESC')
    year_options = [d.year for d in years]

    total_clients = User.objects.filter(is_staff=False, is_superuser=False).count()

    recent_logs = LogEntry.objects.all().order_by('-created_at')[:50]

    email_folders = list(email_folders_qs)

    context = {
        'dashboard_records': page_obj,
        'all_records': records,
        'total_records': total_records,
        'whatsapp_count': whatsapp_count,
        'gmail_count': gmail_count,
        'sms_count': sms_count,
        'total_clients': total_clients,
        'recent_logs': recent_logs,
        'email_folders': email_folders,
        'is_admin': is_admin,
        'company_name': company_name,
        'mc_number': mc_number,
        'number_of_trucks': number_of_trucks,
        'year_options': year_options,
        'page_obj': page_obj,
        'per_page': per_page,
    }
    return render(request, 'dashboard.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def create_dashboard_record(request):
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        email = data.get('email')
        phone_number = data.get('phone_number')
        record_type = data.get('type')
        google_drive_link = data.get('google_drive_link', '')
        
        # if not all([email, phone_number, record_type]):
        #     return JsonResponse({
        #         'status': 'error',
        #         'message': 'Missing required fields: email, phone_number, type'
        #     }, status=400)
        
        if record_type not in ['whatsapp', 'gmail', 'sms']:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid type. Must be: whatsapp, gmail, or sms'
            }, status=400)
        
        if email:
            user = User.objects.filter(email=email).first()
        elif phone_number:
            user = User.objects.filter(phone_number=phone_number).first()
        else:
            user = User.objects.filter(is_superuser=True).first()

        # if user_email:
        #     try:
        #         user = User.objects.get(email=user_email)
        #     except User.DoesNotExist:
        #         return JsonResponse({
        #             'status': 'error',
        #             'message': f'User with email {user_email} not found'
        #         }, status=404)
        # else:
        #     user = User.objects.first()
        
        if not user:
            return JsonResponse({
                'status': 'error',
                'message': 'No admin user found. Please create an admin user first.'
            }, status=400)
        
        dashboard_record = Dashboard.objects.create(
            user=user,
            email=email,
            phone_number=phone_number,
            type=record_type,
            google_drive_link=google_drive_link
        )
        try:
            LogEntry.objects.create(
                user=user,
                level='info',
                event='dashboard_record_created',
                message=f'Created {record_type} record for {email}',
                related_model='Dashboard',
                related_id=str(dashboard_record.id)
            )
        except Exception:
            pass
        
        return JsonResponse({
            'status': 'success',
            'message': 'Dashboard record created successfully',
            'data': {
                'id': dashboard_record.id,
                'email': dashboard_record.email,
                'phone_number': dashboard_record.phone_number,
                'type': dashboard_record.type,
                'google_drive_link': dashboard_record.google_drive_link,
                'created_date': dashboard_record.created_date.isoformat(),
                'user': dashboard_record.user.email
            }
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON format'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def search_email_records(request):
    try:
        if request.method == 'POST':
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST
            email = data.get('email')
            phone_number = data.get('phone_number')
        else:
            email = request.GET.get('email')
        
        
        
        from datetime import datetime
        from django.utils import timezone
        
        now = timezone.now()
        current_year = now.year
        current_month = now.month
        current_date = now.date()
        

        all_records = EmailFolder.objects.filter(Q(email=email) | Q(phone_number=phone_number))

        
        data_exists = all_records.exists()
        
        # ---------------------------------------------------
        # 🔍 ADDED: Fetch company_name and mc_number
        # ---------------------------------------------------
        company_name = None
        mc_number = None

        from .models import User, UserData

        user_obj = None

        # Match User by email
        if email:
            user_obj = User.objects.filter(email=email).select_related("user_data").first()

        # If not found by email, try matching phone number inside UserData.phone_number
        if not user_obj and phone_number:
            user_obj = User.objects.filter(user_data__phone_number=phone_number).select_related("user_data").first()

        if user_obj and hasattr(user_obj, "user_data") and user_obj.user_data:
            company_name = user_obj.user_data.company_name
            mc_number = user_obj.user_data.mc_number
        else:
            return JsonResponse({
                'status': 'success',
                'email': email,
                'phone_number': phone_number,
                'user_exists': False,
                'data_exists': False,
                'has_current_year': False,
                'has_current_month': False,
                'has_today': False,
                'company_name': company_name,
                'mc_number': mc_number,
                'message': 'No user Found'
            }, status=200)
        # ---------------------------------------------------
        
        if not data_exists:
            return JsonResponse({
                'status': 'success',
                'email': email,
                'phone_number': phone_number,
                'user_exists': True,
                'data_exists': False,
                'has_current_year': False,
                'has_current_month': False,
                'has_today': False,
                'company_name': company_name,
                'mc_number': mc_number,
                'message': 'No folder records found for this email'
            }, status=200)
        company_name_mc_number_name = f"{company_name}_{mc_number}"
        year_records = all_records.filter(folder_year=current_year)
        month_records = year_records.filter(folder_month=current_month)
        today_records = month_records.filter(folder_date=current_date)
        company_name_mc_number_name = all_records.filter(company_name_mc_number=company_name_mc_number_name)
        
        has_current_year = year_records.exists()
        has_current_month = month_records.exists()
        has_today = today_records.exists()
        has_company_name_mc_number_name = company_name_mc_number_name.exists()
        
        response_data = {
            'status': 'success',
            'email': email,
            'phone_number': phone_number,
            'user_exists': True,
            'data_exists': True,
            'has_current_year': has_current_year,
            'has_current_month': has_current_month,
            'has_company_name_mc_number_name': has_company_name_mc_number_name,
            'has_today': has_today,
            'company_name': company_name,
            'mc_number': mc_number,
            'message': 'Folder records found for this email'
        }
        
        latest_record = all_records.first()
        if latest_record:
            response_data['company_name_folder_id'] = latest_record.company_name_folder_id
        
        if has_current_year:
            year_record = year_records.first()
            response_data['year_folder_id'] = year_record.year_folder_id
        
        if has_current_month:
            month_record = month_records.first()
            response_data['month_folder_id'] = month_record.month_folder_id
        
        if has_today:
            today_record = today_records.first()
            response_data['date_folder_id'] = today_record.date_folder_id
        
        if has_company_name_mc_number_name:
            company_name_mc_number_name_record = company_name_mc_number_name.first()
            response_data['company_name_folder_id'] = company_name_mc_number_name_record.company_name_folder_id
        
        return JsonResponse(response_data, status=200)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON format'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def create_email_folder(request):
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        email = data.get('email')
        company_name_folder_id = data.get('company_name_folder_id')
        year_folder_id = data.get('year_folder_id')
        month_folder_id = data.get('month_folder_id')
        date_folder_id = data.get('date_folder_id')
        folder_year = data.get('folder_year')
        folder_month = data.get('folder_month')
        folder_date = data.get('folder_date')
        phone_number = data.get('phone_number')
        company_name_mc_number = data.get('company_name_mc_number')
        
        if not all([company_name_folder_id, year_folder_id, month_folder_id, date_folder_id, folder_year, folder_month, folder_date]):
            return JsonResponse({
                'status': 'error',
                'message': 'Missing required fields: email, company_name_folder_id, year_folder_id, month_folder_id, date_folder_id, folder_year, folder_month, folder_date'
            }, status=400)
        
        from datetime import datetime
        try:
            folder_year = int(folder_year)
            folder_month = int(folder_month)
            if isinstance(folder_date, str):
                folder_date = datetime.strptime(folder_date, '%Y-%m-%d').date()
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Invalid date format. folder_year and folder_month must be integers, folder_date must be YYYY-MM-DD format'
            }, status=400)
        
        email_folder = EmailFolder.objects.create(
            email=email,
            phone_number=phone_number,
            company_name_folder_id=company_name_folder_id,
            company_name_mc_number=company_name_mc_number,
            year_folder_id=year_folder_id,
            month_folder_id=month_folder_id,
            date_folder_id=date_folder_id,
            folder_year=folder_year,
            folder_month=folder_month,
            folder_date=folder_date
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Email folder record created successfully',
            'data': {
                'id': email_folder.id,
                'email': email_folder.email,
                'company_name_folder_id': email_folder.company_name_folder_id,
                'year_folder_id': email_folder.year_folder_id,
                'month_folder_id': email_folder.month_folder_id,
                'date_folder_id': email_folder.date_folder_id,
                'folder_year': email_folder.folder_year,
                'folder_month': email_folder.folder_month,
                'folder_date': email_folder.folder_date.isoformat(),
                'created_at': email_folder.created_at.isoformat(),
                'updated_at': email_folder.updated_at.isoformat()
            }
        }, status=201)
        
    except IntegrityError:
        return JsonResponse({
            'status': 'error',
            'message': 'This folder structure already exists for this email and date'
        }, status=400)
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON format'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def send_to_make_webhook(request):
    # ✅ Extract query params
    email = request.POST.get("email")
    phone_number = request.POST.get("phone_number")

    # ✅ Extract text fields (filename, type)
    filename = request.POST.get("filename")
    media_type = request.POST.get("type")

    # ✅ Extract the file uploaded as binary
    file_obj = request.FILES.get("data")

    # ✅ Prepare multipart/form-data
    files = {
        "file": (file_obj.name, file_obj.read(), file_obj.content_type),
    }

    payload = {
        "email": email,
        "phone_number": phone_number,
        "filename": filename,
        "type": media_type
    }

    url = "https://hook.us2.make.com/43p8rg1tinkdvygclzv2e3wkjf57u9qm"

    try:
        response = requests.post(url, data=payload, files=files)
        return JsonResponse({
            "success": True,
            "status_code": response.status_code,
            "response": response.text
        })
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def create_make_log_entry(request):
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        event = data.get('event')
        message = data.get('message')
        level = data.get('level')
        related_model = ""
        related_id = ""
        user = User.objects.filter(is_superuser=True).first()
        log_entry = LogEntry.objects.create(
            user=user,
            event=event,
            message=message,
            level=level,
            related_model=related_model,
            related_id=related_id
        )
        return JsonResponse({
            'status': 'success',
            'message': 'Make log entry created successfully',
            'data': {
                'id': log_entry.id,
                'event': log_entry.event,
                'message': log_entry.message,
                'level': log_entry.level,
                'related_model': log_entry.related_model,
                'related_id': log_entry.related_id,
                'created_at': log_entry.created_at.isoformat(),
                'updated_at': log_entry.updated_at.isoformat()
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON format'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

