from rest_framework.permissions import BasePermission
from django.conf import settings


class CanViewAdminHistory(BasePermission):
    """
    Allows admins access to pass this.
    """
    DRF_ACTIVITY_TRACKER_PERMISSION = "drf_user_activity_tracker_mongodb.view_activitylog"  # Default Permission
    if hasattr(settings, 'DRF_ACTIVITY_TRACKER_PERMISSION'):
        if isinstance(settings.DRF_ACTIVITY_TRACKER_PERMISSION, str):
            DRF_ACTIVITY_TRACKER_PERMISSION = settings.DRF_ACTIVITY_TRACKER_PERMISSION

    message = 'You do not have permission to view admin history!'
    view_name = DRF_ACTIVITY_TRACKER_PERMISSION

    def has_permission(self, request, view):
        return request.user.has_perm(self.view_name)
