import os
from drf_user_activity_tracker_mongodb.events import Events

if os.environ.get('RUN_MAIN', None) != 'true':
    default_app_config = 'drf_user_activity_tracker_mongodb.apps.LoggerConfig'

ACTIVITY_TRACKER_SIGNAL = Events()
