from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('api/create-record/', views.create_dashboard_record, name='create_dashboard_record'),
    path('api/search-email/', views.search_email_records, name='search_email_records'),
    path('api/create-email-folder/', views.create_email_folder, name='create_email_folder'),
    path('api/send-to-make-webhook/', views.send_to_make_webhook, name='send_to_make_webhook'),
]