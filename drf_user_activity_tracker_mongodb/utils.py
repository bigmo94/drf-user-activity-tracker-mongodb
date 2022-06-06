import collections.abc
import importlib
import re
import warnings
from math import ceil

from bson import ObjectId
from django.apps import apps
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from pymongo import MongoClient

SENSITIVE_KEYS = ['password', 'token', 'access', 'refresh']
if hasattr(settings, 'DRF_ACTIVITY_TRACKER_EXCLUDE_KEYS'):
    if isinstance(settings.DRF_ACTIVITY_TRACKER_EXCLUDE_KEYS, (list, tuple)):
        SENSITIVE_KEYS.extend(settings.DRF_ACTIVITY_TRACKER_EXCLUDE_KEYS)


def get_headers(request=None):
    """
        Function:       get_headers(self, request)
        Description:    To get all the headers from request
    """
    regex = re.compile('^HTTP_')
    return dict((regex.sub('', header), value) for (header, value)
                in request.META.items() if header.startswith('HTTP_'))


def get_client_ip(request):
    try:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    except:
        return ''


def is_activity_tracker_enabled():
    drf_activity_tracker_database = False
    if hasattr(settings, 'DRF_ACTIVITY_TRACKER_DATABASE'):
        drf_activity_tracker_database = settings.DRF_ACTIVITY_TRACKER_DATABASE

    drf_activity_tracker_signal = False
    if hasattr(settings, 'DRF_ACTIVITY_TRACKER_SIGNAL'):
        drf_activity_tracker_signal = settings.DRF_ACTIVITY_TRACKER_SIGNAL
    return drf_activity_tracker_database or drf_activity_tracker_signal


def database_log_enabled():
    drf_activity_tracker_database = False
    if hasattr(settings, 'DRF_ACTIVITY_TRACKER_DATABASE'):
        drf_activity_tracker_database = settings.DRF_ACTIVITY_TRACKER_DATABASE
    return drf_activity_tracker_database


def mask_sensitive_data(data):
    """
    Hides sensitive keys specified in sensitive_keys settings.
    Loops recursively over nested dictionaries.
    """

    if not isinstance(data, dict):
        return data

    for key, value in data.items():
        if key in SENSITIVE_KEYS:
            data[key] = "***FILTERED***"

        if isinstance(value, dict):
            data[key] = mask_sensitive_data(data[key])

        if isinstance(value, list):
            data[key] = [mask_sensitive_data(item) for item in data[key]]

    return data


class MongoConnection(object):
    def __init__(self):
        client = MongoClient(settings.DRF_ACTIVITY_TRACKER_MONGO_CONNECTION)

        self.db = client[settings.DRF_ACTIVITY_TRACKER_MONGO_DB_NAME]
        self.collection = self.db[settings.DRF_ACTIVITY_TRACKER_MONGO_DB_COLLECTION_NAME]


class MyCollection(MongoConnection):

    def data_count(self, user_id=None, url_name=None, status_code=None, time_delta=None):
        filter_params = {}
        if user_id:
            filter_params.update({'user_id': user_id})
        if url_name:
            filter_params.update({'url_name': url_name})
        if status_code:
            filter_params.update({'status_code': {'$gte': status_code, '$lt': status_code + 100}})
        if time_delta:
            filter_params.update({'created_time': time_delta})
        return self.collection.count_documents(filter_params)

    def save(self, obj_list):
        self.collection.insert_many(obj_list)

    def list(self, user_id=None, url_name=None, status_code=None, time_delta=None, api=False, dataset_limit=0, skip=0):
        filter_params = {}
        if user_id:
            filter_params.update({'user_id': user_id})
        if api:
            limit = 100
            if hasattr(settings, 'DRF_ACTIVITI_API_LIMIT'):
                if isinstance(settings.DRF_ACTIVITI_API_LIMIT, (tuple, list)):
                    limit = settings.DRF_ACTIVITI_API_LIMIT
            return list(self.collection.find(filter_params).sort('created_time', -1).limit(limit))
        if url_name:
            filter_params.update({'url_name': url_name})
        if status_code:
            filter_params.update({'status_code': {'$gte': status_code, '$lt': status_code + 100}})
        if time_delta:
            filter_params.update({'created_time': time_delta})
        return list(self.collection.find(filter_params).sort('created_time', -1).limit(dataset_limit).skip(skip))

    def detail(self, pk):
        try:
            pk = ObjectId(pk)
        except:
            return None
        return self.collection.find_one({'_id': pk})


def get_all_url_names():
    list_of_all_urls = list()
    list_of_url_name = list()
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
            if url.name:
                list_of_url_name.append(url.name)

    return list_of_url_name


class ParamsHandler:

    def __init__(self, request):
        self.params = request.GET

    def get_url_name(self):
        return self.params.get('url_name')

    def get_search_value(self):
        search_params = self.params.get('q')
        if search_params and search_params.isdigit():
            return int(search_params)

    def get_status(self):
        status_code = self.params.get('status')
        if status_code and status_code.isdigit():
            return int(status_code)

    def get_time_delta(self):
        now = timezone.now()
        today = now.today()
        return {
            'today': {'$lte': now, '$gt': today.replace(hour=0, minute=0, second=0, microsecond=0)},
            'past_7_days': {'$lte': now,
                            '$gt': today.replace(hour=0, minute=0, second=0, microsecond=0) - timezone.timedelta(
                                days=7)},
            'this_month': {'$lte': today,
                           '$gt': today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)},
            'this_year': {'$lte': today,
                          '$gt': today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)},
        }.get(self.params.get('created_time'))


class CustomPaginator(Paginator):

    def __init__(self, dataset, data_count, per_page, orphans=0,
                 allow_empty_first_page=True):
        self.data_count = data_count
        self.dataset = dataset
        self.per_page = int(per_page)
        self.orphans = int(orphans)
        self.allow_empty_first_page = allow_empty_first_page

    def page(self, number):
        """Return a Page object for the given 1-based page number."""
        number = self.validate_number(number)
        return self._get_page(self.dataset, number, self)

    @cached_property
    def count(self):
        return None

    @cached_property
    def num_pages(self):
        """Return the total number of pages."""
        if self.data_count == 0 and not self.allow_empty_first_page:
            return 0
        hits = max(1, self.data_count - self.orphans)
        return ceil(hits / self.per_page)


class Page(collections.abc.Sequence):

    def __init__(self, dataset, number, paginator):
        self.dataset = dataset
        self.number = number
        self.paginator = paginator

    def __repr__(self):
        return '<Page %s of %s>' % (self.number, self.paginator.num_pages)

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, index):
        if not isinstance(index, (int, slice)):
            raise TypeError(
                'Page indices must be integers or slices, not %s.'
                % type(index).__name__
            )
        return self.dataset

    def has_next(self):
        return self.number < self.paginator.num_pages

    def has_previous(self):
        return self.number > 1

    def has_other_pages(self):
        return self.has_previous() or self.has_next()

    def next_page_number(self):
        return self.paginator.validate_number(self.number + 1)

    def previous_page_number(self):
        return self.paginator.validate_number(self.number - 1)

    def start_index(self):
        """
        Return the 1-based index of the first object on this page,
        relative to total objects in the paginator.
        """
        # Special case, return zero if no items.
        if self.paginator.count == 0:
            return 0
        return (self.paginator.per_page * (self.number - 1)) + 1

    def end_index(self):
        """
        Return the 1-based index of the last object on this page,
        relative to total objects found (hits).
        """
        # Special case for the last page because there can be orphans.
        if self.number == self.paginator.num_pages:
            return self.paginator.count
        return self.number * self.paginator.per_page
