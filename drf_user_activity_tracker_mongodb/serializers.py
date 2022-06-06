from django.conf import settings
from rest_framework import serializers


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
