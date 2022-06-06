from django.db import models
from django.utils.translation import ugettext_lazy as _


class ActivityLog:
    class Meta:
        app_label = 'drf_user_activity_tracker_mongodb'
        object_name = 'activity_log'
        model_name = module_name = 'activity_log'
        verbose_name = _('activity log')
        verbose_name_plural = _('activity logs')
        abstract = False
        swapped = False
        app_config = ""

    objects = models.Manager()
    _meta = Meta()
