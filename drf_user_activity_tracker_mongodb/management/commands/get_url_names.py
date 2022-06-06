import importlib
import json

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'get all url names'

    def handle(self, *args, **options):

        list_of_all_urls = list()
        for name, app in apps.app_configs.items():
            mod_to_import = f'{name}.urls'
            try:
                urls = getattr(importlib.import_module(mod_to_import), 'urlpatterns')
                list_of_all_urls.extend(urls)
            except ImportError as ex:
                # is an app without urls
                pass
        for url in list_of_all_urls:
            if hasattr(url, 'name'):
                settings.DRF_ACTIVITY_TRACKER_EVENT_NAME.update({url.name: ''})

        result = json.dumps(settings.DRF_ACTIVITY_TRACKER_EVENT_NAME, indent=3)
        self.stdout.write(self.style.SUCCESS(result))
