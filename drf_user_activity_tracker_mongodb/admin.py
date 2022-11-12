from django.conf import settings
from django import get_version
from django.contrib import admin
from django.contrib import messages
from django.core.paginator import PageNotAnInteger, EmptyPage
from django.shortcuts import redirect, reverse
from django.template.response import TemplateResponse
from django.urls import path
from drf_user_activity_tracker_mongodb.utils import (MyCollection,
                                                     get_all_url_names,
                                                     ParamsHandler,
                                                     CustomPaginator,
                                                     database_log_enabled)

if database_log_enabled():
    from drf_user_activity_tracker_mongodb.models import ActivityLog


    @admin.register(ActivityLog)
    class ActivityLogAdmin(admin.ModelAdmin):
        model = ActivityLog

        def get_urls(self):
            info = "{}_{}_changelist".format(self.model._meta.app_label, self.model._meta.model_name)
            detail = "{}_{}_change".format(self.model._meta.app_label, self.model._meta.model_name)

            return [
                path(r'', self.activity_log_view, name=info),
                path(r'<str:pk>/change/', self.activity_log_detail_view, name=detail)
            ]

        def activity_log_view(self, request):
            params = ParamsHandler(request)

            url_names_list = get_all_url_names()
            url_name = params.get_url_name()
            search_value = params.get_search_value()
            status_code = params.get_status()
            time_delta = params.get_time_delta()

            data_count = MyCollection().data_count(url_name=url_name, user_id=search_value, status_code=status_code,
                                                   time_delta=time_delta)

            dataset_limit = 50
            if hasattr(settings, 'DRF_ACTIVITY_TRACKER_DJANGO_ADMIN_LIMIT'):
                if isinstance(settings.DRF_ACTIVITY_TRACKER_DJANGO_ADMIN_LIMIT, int):
                    dataset_limit = settings.DRF_ACTIVITY_TRACKER_DJANGO_ADMIN_LIMIT

            page = request.GET.get('page', "")

            if page.isdigit():
                page = int(page)
            else:
                page = 1

            skip = (page - 1) * dataset_limit

            dataset = MyCollection().list(url_name=url_name, user_id=search_value, status_code=status_code,
                                          time_delta=time_delta, dataset_limit=dataset_limit, skip=skip)

            paginator = CustomPaginator(dataset=dataset, data_count=data_count, per_page=dataset_limit)

            try:
                page_object = paginator.page(page)
            except PageNotAnInteger:
                page_object = paginator.page(1)
            except EmptyPage:
                page_object = paginator.page(paginator.num_pages)

            context = dict(self.admin_site.each_context(request), dataset=dataset, page_object=page_object,
                           url_names=url_names_list,
                           count=data_count)

            if int(get_version()[0]) == 2:
                return TemplateResponse(request, "activity_log/admin/change_list_v2.html", context=context)

            return TemplateResponse(request, "activity_log/admin/change_list_v3.html", context=context)

        def activity_log_detail_view(self, request, pk=None):
            data = MyCollection().detail(pk)
            if not data:
                messages.warning(request, f"Log with ID '{pk}' doesn’t exist. Perhaps it was deleted?")
                return redirect(reverse('admin:index'))
            context = dict(self.admin_site.each_context(request), data=data)
            return TemplateResponse(request, "activity_log/admin/change_detail.html", context=context)
