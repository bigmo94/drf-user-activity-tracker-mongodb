import ipaddress
import json
import pathlib
import time

import jwt
import pygeoip
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import resolve
from django.utils import timezone
from rest_framework.parsers import MultiPartParser

from drf_user_activity_tracker_mongodb import ACTIVITY_TRACKER_SIGNAL
from drf_user_activity_tracker_mongodb.start_logger_when_server_starts import LOGGER_THREAD
from drf_user_activity_tracker_mongodb.utils import get_headers, get_client_ip, mask_sensitive_data

User = get_user_model()

"""
File: activity_tracker_middleware.py
Class: ActivityTrackerMiddleware
"""


class ActivityTrackerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

        self.DRF_ACTIVITY_TRACKER_DATABASE = False
        if hasattr(settings, 'DRF_ACTIVITY_TRACKER_DATABASE'):
            self.DRF_ACTIVITY_TRACKER_DATABASE = settings.DRF_ACTIVITY_TRACKER_DATABASE

        self.DRF_ACTIVITY_TRACKER_SIGNAL = False
        if hasattr(settings, 'DRF_ACTIVITY_TRACKER_SIGNAL'):
            self.DRF_ACTIVITY_TRACKER_SIGNAL = settings.DRF_ACTIVITY_TRACKER_SIGNAL

        self.DRF_ACTIVITY_TRACKER_PATH_TYPE = 'ABSOLUTE'
        if hasattr(settings, 'DRF_ACTIVITY_TRACKER_PATH_TYPE'):
            if settings.DRF_ACTIVITY_TRACKER_PATH_TYPE in ['ABSOLUTE', 'RAW_URI', 'FULL_PATH']:
                self.DRF_ACTIVITY_TRACKER_PATH_TYPE = settings.DRF_ACTIVITY_TRACKER_PATH_TYPE

        self.DRF_ACTIVITY_TRACKER_SKIP_URL_NAME = ['user_history', 'admin_history']
        if hasattr(settings, 'DRF_ACTIVITY_TRACKER_SKIP_URL_NAME'):
            if isinstance(settings.DRF_ACTIVITY_TRACKER_SKIP_URL_NAME, (tuple, list)):
                self.DRF_ACTIVITY_TRACKER_SKIP_URL_NAME.extend(settings.DRF_ACTIVITY_TRACKER_SKIP_URL_NAME)

        self.DRF_ACTIVITY_TRACKER_DONT_SKIP_URL_NAME = []
        if hasattr(settings, 'DRF_ACTIVITY_TRACKER_DONT_SKIP_URL_NAME'):
            if isinstance(settings.DRF_ACTIVITY_TRACKER_DONT_SKIP_URL_NAME, (tuple, list)):
                self.DRF_ACTIVITY_TRACKER_DONT_SKIP_URL_NAME.extend(settings.DRF_ACTIVITY_TRACKER_DONT_SKIP_URL_NAME)

        self.DRF_ACTIVITY_TRACKER_SKIP_NAMESPACE = []
        if hasattr(settings, 'DRF_ACTIVITY_TRACKER_SKIP_NAMESPACE'):
            if isinstance(settings.DRF_ACTIVITY_TRACKER_SKIP_NAMESPACE, (tuple, list)):
                self.DRF_ACTIVITY_TRACKER_SKIP_NAMESPACE = settings.DRF_ACTIVITY_TRACKER_SKIP_NAMESPACE

        self.DRF_ACTIVITY_TRACKER_METHODS = []
        if hasattr(settings, 'DRF_ACTIVITY_TRACKER_METHODS'):
            if isinstance(settings.DRF_ACTIVITY_TRACKER_METHODS, (tuple, list)):
                self.DRF_ACTIVITY_TRACKER_METHODS = settings.DRF_ACTIVITY_TRACKER_METHODS

        self.DRF_ACTIVITY_TRACKER_TOKEN_PAYLOAD_KEYS = ['user_id']
        if hasattr(settings, 'DRF_ACTIVITY_TRACKER_TOKEN_PAYLOAD_KEYS'):
            if isinstance(settings.DRF_ACTIVITY_TRACKER_TOKEN_PAYLOAD_KEYS, (tuple, list)):
                self.DRF_ACTIVITY_TRACKER_TOKEN_PAYLOAD_KEYS.extend(settings.DRF_ACTIVITY_TRACKER_TOKEN_PAYLOAD_KEYS)

    def __call__(self, request):
        
        method = request.method

        # Log only registered methods if available.
        if len(self.DRF_ACTIVITY_TRACKER_METHODS) > 0 and method not in self.DRF_ACTIVITY_TRACKER_METHODS:
            return self.get_response(request)

        # Run only if logger is enabled.
        if self.DRF_ACTIVITY_TRACKER_DATABASE or self.DRF_ACTIVITY_TRACKER_SIGNAL:

            url_name = resolve(request.path).url_name
            namespace = resolve(request.path).namespace

            # Always skip Admin panel
            if namespace == 'admin':
                return self.get_response(request)

            # Skip for url name
            if url_name in self.DRF_ACTIVITY_TRACKER_SKIP_URL_NAME:
                return self.get_response(request)

            # Skip entire app using namespace
            if namespace in self.DRF_ACTIVITY_TRACKER_SKIP_NAMESPACE:
                return self.get_response(request)

            start_time = time.time()
            request_data = ''
            try:
                if request.content_type.find('application/json') != -1 or request.content_type.find(
                        'application/vnd.api+json') != -1:
                    request_data = json.loads(request.body) if request.body else ''
                elif request.content_type == 'multipart/form-data':
                    parser_obj = MultiPartParser()
                    context = {'request': request}
                    request_data = parser_obj.parse(stream=request._stream, media_type=request.META['CONTENT_TYPE'],
                                                    parser_context=context) if request.body else ''
                    request_data = dict(request_data.data)
            except:
                pass

            # Code to be executed for each request before
            # the view (and later middleware) are called.
            response = self.get_response(request)

            # Code to be executed for each request/response after
            # the view is called.

            header_token = request.META.get("HTTP_AUTHORIZATION")
            algorithm = 'HS256'
            if hasattr(settings, "JWT_ALGORITHM") and isinstance(settings.JWT_ALGORITHM, str):
                algorithm = settings.JWT_ALGORITHM

            payload_data = {}
            if header_token:
                try:
                    token = header_token.split()[1]
                    user_token = jwt.decode(jwt=token, key=settings.SECRET_KEY, algorithms=[algorithm])
                except:
                    return response
                for key in self.DRF_ACTIVITY_TRACKER_TOKEN_PAYLOAD_KEYS:
                    payload_data[key] = user_token.get(key)

            elif hasattr(response, 'data') and isinstance(response.data, dict) and response.data.get('access'):
                try:
                    user_token = jwt.decode(jwt=response.data.get('access'), key=settings.SECRET_KEY,
                                            algorithms=[algorithm])
                except:
                    return response
                for key in self.DRF_ACTIVITY_TRACKER_TOKEN_PAYLOAD_KEYS:
                    payload_data[key] = user_token.get(key)

            elif url_name in self.DRF_ACTIVITY_TRACKER_DONT_SKIP_URL_NAME:
                for key in self.DRF_ACTIVITY_TRACKER_TOKEN_PAYLOAD_KEYS:
                    payload_data[key] = None
            else:
                return response

            headers = get_headers(request=request)


            if response.get('content-type') in ('application/json', 'application/vnd.api+json',):
                if getattr(response, 'streaming', False):
                    response_body = '** Streaming **'
                else:
                    if isinstance(response.content, bytes):
                        response_body = json.loads(response.content.decode())
                    else:
                        response_body = json.loads(response.content)
                if self.DRF_ACTIVITY_TRACKER_PATH_TYPE == 'ABSOLUTE':
                    api = request.build_absolute_uri()
                elif self.DRF_ACTIVITY_TRACKER_PATH_TYPE == 'FULL_PATH':
                    api = request.get_full_path()
                elif self.DRF_ACTIVITY_TRACKER_PATH_TYPE == 'RAW_URI':
                    api = request.get_raw_uri()
                else:
                    api = request.build_absolute_uri()
                ip = get_client_ip(request)
                if ipaddress.ip_address(ip).version == 4:
                    try:
                        country_name = pygeoip.GeoIP(
                            '{}/geo_databases/GeoIP.dat'.format(pathlib.Path(__file__).parent.parent),
                            pygeoip.MEMORY_CACHE).country_name_by_addr(ip)
                    except:
                        country_name = ''
                else:
                    try:
                        country_name = pygeoip.GeoIP(
                            '{}/geo_databases/GeoIPv6.dat'.format(pathlib.Path(__file__).parent.parent),
                            pygeoip.MEMORY_CACHE).country_name_by_addr(ip)
                    except:
                        country_name = ''
                data = dict(
                    url_name=url_name,
                    url_path=request.path,
                    api=api,
                    headers=mask_sensitive_data(headers),
                    body=mask_sensitive_data(request_data),
                    method=method,
                    client_ip_address=ip,
                    response=mask_sensitive_data(response_body),
                    status_code=response.status_code,
                    execution_time=time.time() - start_time,
                    created_time=timezone.now(),
                    country=country_name,
                )
                data.update(payload_data)
                if self.DRF_ACTIVITY_TRACKER_DATABASE:
                    if LOGGER_THREAD:
                        LOGGER_THREAD.put_log_data(data=data)
                if self.DRF_ACTIVITY_TRACKER_SIGNAL:
                    ACTIVITY_TRACKER_SIGNAL.listen(**data)
            else:
                return response

        else:
            response = self.get_response(request)
        return response
