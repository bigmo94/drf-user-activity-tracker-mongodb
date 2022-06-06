from django.urls import path
from drf_user_activity_tracker_mongodb.views import ActivityLogView, ActivityLogAdminView

app_name = "activity_log"


urlpatterns = [
    path('user-history/', ActivityLogView.as_view(), name='user_history'),
    path('admin-history/', ActivityLogAdminView.as_view(), name='admin_history'),
]


