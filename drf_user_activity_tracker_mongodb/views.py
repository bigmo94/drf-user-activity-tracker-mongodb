from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response

from drf_user_activity_tracker_mongodb.utils import MyCollection
from drf_user_activity_tracker_mongodb.serializers import ActivityLogSerializer, ActivityLogAdminSerializer
from drf_user_activity_tracker_mongodb.permissions import CanViewAdminHistory


class ActivityLogView(GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ActivityLogSerializer

    def get(self, request):
        response = MyCollection().list(user_id=self.request.user.id, api=True)
        serializer = self.get_serializer(instance=response, many=True)
        return Response(serializer.data)


class ActivityLogAdminView(GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, CanViewAdminHistory]
    serializer_class = ActivityLogAdminSerializer

    def get(self, request):
        response = MyCollection().list(api=True)
        serializer = self.get_serializer(instance=response, many=True)
        return Response(serializer.data)
