from django.db import models
from django.utils.translation import ugettext_lazy as _


class ActivityLog(models.Model):
    class Meta:
        managed = False
        verbose_name = _('activity log')
        verbose_name_plural = _('activity logs')
