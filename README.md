# DRF User Activity Tracker Mongodb
## _Log All User Activities_

![version](https://img.shields.io/badge/version-1.4.1-blue.svg)
[![Open Source](https://badges.frapsoft.com/os/v1/open-source.svg?v=103)](https://opensource.org/)
<a href="https://github.com/bigmo94/drf-user-activity-tracker-mongodb"><img src="https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white" alt="GitHub"/></a>

> [!WARNING]  
> You must update to the latest version.

An API Logger of User Activity for your Django Rest Framework project.

It logs all the API information for content type "application/json" in mongo database.

Note: It logs just API information for registered user. (Anonymous User Activities are ignored. But It's possible to log api without user id by add their url names in DRF_ACTIVITY_TRACKER_DONT_SKIP_URL_NAME attribute in settings.py) 

1. User_ID
2. URL_PATH
3. URL_NAME
4. Request Body
5. Request Headers
6. Request Method
7. API Response
8. Status Code
9. API Call Time
10. Server Execution Time
11. Client IP Address
12. Client Country Name

You can log API information into the database or listen to the logger signals for different use-cases, or you can do both.

* The logger usage a separate thread to run, so it won't affect your API response time.

## Requirements
* Django
* Django Rest Framework
* Simple JWT
* Pymongo
* pygeoip

## Installation

Install or add drf-user-activity-tracker.
```shell script
pip install drf-user-activity-tracker-mongodb
```

Add in INSTALLED_APPS
```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'drf_user_activity_tracker_mongodb',  #  Add here
]
```

Add in MIDDLEWARE
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'drf_user_activity_tracker_mongodb.middleware.activity_tracker_middleware.ActivityTrackerMiddleware', # Add here
]
```

#### * Add these lines in Django settings file.
Note: `The user_id must be in the access token's payload. and 'access' key must be in login response data.`
## Store logs into the database
Log every request into the database.
```python
DRF_ACTIVITY_TRACKER_DATABASE = True  # Default to False
```

* Logs will be available in Django Admin Panel.

* The search bar will search in Request Body, Response, Headers and API URL.


Note: You don't need to migrate if you don't want use history api'.

## Set Mongodb settings
Specify the mongodb config:
```
DRF_ACTIVITY_TRACKER_MONGO_DB_NAME = 'database_name'
DRF_ACTIVITY_TRACKER_MONGO_DB_COLLECTION_NAME = 'collection_name'
DRF_ACTIVITY_TRACKER_MONGO_CONNECTION = 'mongodb://{username}:{password}@{host}'
```
## Limit rows of django admin per page
Add this line to settings.py:
```
DRF_ACTIVITY_TRACKER_DJANGO_ADMIN_LIMIT = 50 , # Default is 50
```
## To listen for the logger signals.
Listen to the signal as soon as any API is called. So you can log the API data into a file or for different use-cases.
```python
DRF_ACTIVITY_TRACKER_SIGNAL = True  # Default to False
```
Example code to listen to the API Logger Signal.
```python
"""
Import ACTIVITY_TRACKER_SIGNAL
"""
from drf_user_activity_tracker import ACTIVITY_TRACKER_SIGNAL


"""
Create a function that is going to listen to the API logger signals.
"""
def listener_one(**kwargs):
    print(kwargs)

def listener_two(**kwargs):
    print(kwargs)

"""
It will listen to all the API logs whenever an API is called.
You can also listen signals in multiple functions.
"""
ACTIVITY_TRACKER_SIGNAL.listen += listener_one
ACTIVITY_TRACKER_SIGNAL.listen += listener_two

"""
Unsubscribe to signals.
"""

ACTIVITY_TRACKER_SIGNAL.listen -= listener_one
```

### Queue

DRF ACTIVITY TRACKER usage queue to hold the logs before inserting into the database. Once queue is full, it bulk inserts into the database.

Specify the queue size.
```python
DRF_ACTIVITY_TRACKER_QUEUE_MAX_SIZE = 50  # Default to 50 if not specified.
```

### Interval

DRF ACTIVITY TRACKER also waits for a period of time. If queue is not full and there are some logs to be inserted, it inserts after interval ends.

Specify an interval (In Seconds).
```python
DRF_ACTIVITY_TRACKER_INTERVAL = 10  # In Seconds, Default to 10 seconds if not specified.
```
Note: The API call time (created_time) is a timezone aware datetime object. It is actual time of API call irrespective of interval value or queue size.
### Skip namespace
You can skip the entire app to be logged into the database by specifying namespace of the app as list.
```python
DRF_ACTIVITY_TRACKER_SKIP_NAMESPACE = ['APP_NAMESPACE1', 'APP_NAMESPACE2']
```

### Skip URL Name
You can also skip any API to be logged by using url_name of the API.
```python
DRF_ACTIVITY_TRACKER_SKIP_URL_NAME = ['url_name1', 'url_name2']
```

### DON'T Skip URL Name
You can also set `DRF_ACTIVITY_TRACKER_DONT_SKIP_URL_NAME` in settings.py to logs api that does not have a user id.
```python
DRF_ACTIVITY_TRACKER_DONT_SKIP_URL_NAME = ['url_name1', 'url_name2']
```

Note: It does not log Django Admin Panel API calls and history logs list API calls.

### Hide Sensitive Data From Logs
You may wish to hide sensitive information from being exposed in the logs. 
You do this by setting `DRF_ACTIVITY_TRACKER_EXCLUDE_KEYS` in settings.py to a list of your desired sensitive keys. 
The default is
```python
DRF_ACTIVITY_TRACKER_EXCLUDE_KEYS = ['password', 'token', 'access', 'refresh']
# Sensitive data will be replaced with "***FILTERED***".
```

### Want to log only selected request methods? (Optional)
You can log only selected methods by specifying `DRF_ACTIVITY_TRACKER_METHODS` in settings.py.
```python
DRF_ACTIVITY_TRACKER_METHODS = ['GET', 'POST', 'DELETE', 'PUT']  # Default to empty list (Log all the requests).
```

### Want to log token's payload keys?
If you add some keys to payload of token, and you want to log these keys into db, you can do this by setting `DRF_ACTIVITY_TRACKER_TOKEN_PAYLOAD_KEYS` in settings.py.
Note: the user_id is logged by default, and you don't need to add this key.
```python
# Example
token_payload = {
  "token_type": "access",
  "exp": 1313131313,
  "jti": "32b32caa7c4c04d3ab7050175e54680d1",
  "user_id": 13,
  "protect_key": "13CC13DSF424FSF",
  "company_id": "13"
}
DRF_ACTIVITY_TRACKER_TOKEN_PAYLOAD_KEYS = ['company_id', 'protect_key']
```

### Want to see the API information in local timezone? (Optional)
You can also change the timezone by specifying `DRF_ACTIVITY_TRACKER_TIMEDELTA` in settings.py.
It won't change the Database timezone. It will still remain UTC or the timezone you have defined.
```python
DRF_ACTIVITY_TRACKER_TIMEDELTA = 330 # UTC + 330 Minutes = IST (5:Hours, 30:Minutes ahead from UTC) 
# Specify in minutes.
```
```python
# Yoc can specify negative values for the countries behind the UTC timezone.
DRF_ACTIVITY_TRACKER_TIMEDELTA = -30  # Example
```

### API with or without Host
You can specify an endpoint of API should have absolute URI or not by setting this variable in DRF settings.py file.
```python
DRF_ACTIVITY_TRACKER_PATH_TYPE = 'ABSOLUTE'  # Default to ABSOLUTE if not specified
# Possible values are ABSOLUTE, FULL_PATH or RAW_URI
```

Considering we are accessing the following URL: http://127.0.0.1:8000/api/v1/?page=123
DRF_ACTIVITY_TRACKER_PATH_TYPE possible values are:
1. ABSOLUTE (Default) :   

    Function used ```request.build_absolute_uri()```
    
    Output: ```http://127.0.0.1:8000/api/v1/?page=123```
    
2. FULL_PATH

    Function used ```request.get_full_path()```
    
    Output: ```/api/v1/?page=123```
    
3. RAW_URI

    Function used ```request.get_raw_uri()```
    
    Output: ```http://127.0.0.1:8000/api/v1/?page=123```
    
    Note: Similar to ABSOLUTE but skip allowed hosts protection, so may return an insecure URI.



### API Call For History Of Activities By Users Or Admin 

Add in your_project_root/project_name/urls.py
```
urlpatterns = [
    path('service_admin_zone/', admin.site.urls),
    path('activity-logs/', include('drf_user_activity_tracker.urls')),
]
```
##### Access to this API by following URL:
{{ your_base_url }}/activity-logs/user-history/
{{ your_base_url }}/activity-logs/admin-history/

`for calling admin history api; you must have 'can view avtivity log' permission. or add DRF_ACTIVITY_TRACKER_PERMISSION in settings.py and add your permission in a string format.`
```
DRF_ACTIVITY_TRACKER_PERMISSION = 'customers.can_view_logs'
```
##### The response includes these:

1. id
2. event_name
3. client_ip_address
4. created_time


##### available query param filters
* created_time_after
* created_time_before
* limit
* offset

#### Set event names

By default event name is url_name. You can also change the event name by specifying `DRF_ACTIVITY_TRACKER_EVENT_NAME` in settings.py.
you can run this command to get dictionary of all urls name:
```
python manage.py get_url_names
```
and then copy the dictionary to settings.py:
```python
DRF_ACTIVITY_TRACKER_EVENT_NAME = {
        'user_register': 'Registeration',
        'orders-redeem': 'Redeem Card',
}
DRF_ACTIVITI_API_LIMIT = 100  #for count of api results, default is 100.
```
#### Prevent user to see some activities in history endpoint
By default all activities are shown in user history endpoint. you can add specific url name that you don't want to show to the user in `DRF_ACTIVITI_API_UNNECESSARY_URL_NAME` attribute in settings.py and then the user can not be able to see them. 
Note: This attribute must be a list.

#### Excluding specific url names in django admin panel
Note: In django admin panel you can filter logs by url name. some url name do not appear in filter list. you can set `DRF_ACTIVITY_TRACKER_URL_NAMES` in settings with the list of url names that you want to be filtered by.


