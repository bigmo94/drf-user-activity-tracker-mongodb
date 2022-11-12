from datetime import datetime

from django.conf import settings
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class QueryParamsValidatorSerializer(serializers.Serializer):
    created_time_after = serializers.DateField(required=False)
    created_time_before = serializers.DateField(required=False)
    url_name = serializers.CharField(required=False)
    user_id = serializers.IntegerField(required=False)

    def validate(self, attrs):
        if attrs.get("created_time_after") and attrs.get("created_time_before"):
            if attrs.get("created_time_after") > attrs.get("created_time_before"):
                raise ValidationError(_("from time occurred after to time!"))

        # Mongodb does not support date field, these scripts convert date fields to datetime fields
        if attrs.get("created_time_after"):
            created_time_after_date = attrs.get("created_time_after")
            created_time_after_date_time = datetime(year=created_time_after_date.year,
                                                    month=created_time_after_date.month,
                                                    day=created_time_after_date.day)
            attrs['created_time_after'] = created_time_after_date_time

        if attrs.get("created_time_before"):
            created_time_before_date = attrs.get("created_time_before")
            created_time_before_date_time = datetime(year=created_time_before_date.year,
                                                     month=created_time_before_date.month,
                                                     day=created_time_before_date.day,
                                                     hour=23, minute=59, second=59)
            attrs['created_time_before'] = created_time_before_date_time

        return attrs


class ActivityLogSerializer(serializers.Serializer):
    _id = serializers.CharField()
    event_name = serializers.SerializerMethodField(read_only=True)
    created_time = serializers.DateTimeField()
    client_ip_address = serializers.CharField()
    url_name = serializers.CharField(max_length=255, write_only=True)

    class Meta:
        fields = ['_id', 'event_name', 'client_ip_address', 'created_time']

    def get_event_name(self, obj):
        event_name = obj.get('url_name', '')
        if hasattr(settings, 'DRF_ACTIVITY_TRACKER_EVENT_NAME'):
            if isinstance(settings.DRF_ACTIVITY_TRACKER_EVENT_NAME, dict):
                event_name = settings.DRF_ACTIVITY_TRACKER_EVENT_NAME.get(obj.get('url_name'), obj.get('url_name'))
                if not event_name:
                    event_name = obj.get('url_name', '')
        return event_name


class ActivityLogAdminSerializer(ActivityLogSerializer):
    user_id = serializers.IntegerField()

    class Meta:
        fields = ['_id', 'user_id', 'event_name', 'client_ip_address', 'created_time']
