from rest_framework import mixins
from rest_framework.generics import GenericAPIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from drf_user_activity_tracker_mongodb.permissions import CanViewAdminHistory
from drf_user_activity_tracker_mongodb.serializers import ActivityLogSerializer, ActivityLogAdminSerializer, \
    DateValidatorSerializer
from drf_user_activity_tracker_mongodb.utils import MyCollection, create_time_delta_for_api


class ActivityLogView(mixins.ListModelMixin, GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ActivityLogSerializer
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        date_validator_serializer = DateValidatorSerializer(data=self.request.query_params)
        date_validator_serializer.is_valid(raise_exception=True)

        created_time_after = date_validator_serializer.validated_data.get("created_time_after")
        created_time_before = date_validator_serializer.validated_data.get("created_time_before")
        time_delta = create_time_delta_for_api(created_time_after, created_time_before)
        if time_delta:
            return MyCollection().api_list(user_id=self.request.user.id, time_delta=time_delta)

        return MyCollection().api_list(user_id=self.request.user.id)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class ActivityLogAdminView(mixins.ListModelMixin, GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, CanViewAdminHistory]
    serializer_class = ActivityLogAdminSerializer
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        date_validator_serializer = DateValidatorSerializer(data=self.request.query_params)
        date_validator_serializer.is_valid(raise_exception=True)

        created_time_after = date_validator_serializer.validated_data.get("created_time_after")
        created_time_before = date_validator_serializer.validated_data.get("created_time_before")
        time_delta = create_time_delta_for_api(created_time_after, created_time_before)

        if time_delta:
            return MyCollection().api_list(time_delta=time_delta)

        return MyCollection().api_list()

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
