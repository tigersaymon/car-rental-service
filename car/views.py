from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .filters import CarFilter
from .models import Car
from .permissions import IsAdminOrIfAuthenticatedReadOnly
from .serializers import (
    CarDetailSerializer,
    CarImageSerializer,
    CarListSerializer,
    CarSerializer,
)


class CarViewSet(ModelViewSet):
    """
    ViewSet for managing Car objects.
    Provides CRUD operations, filtering, searching, ordering,
    and a custom action for uploading car images.
    """

    queryset = Car.objects.all()
    serializer_class = CarSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CarFilter
    search_fields = ["brand", "model"]
    ordering_fields = ["daily_rate", "year"]
    ordering = ["brand"]

    def get_serializer_class(self):
        """
        Return the appropriate serializer class depending on the action.
        - list: CarListSerializer
        - retrieve: CarDetailSerializer
        - upload_image: CarImageSerializer
        - default: CarSerializer
        """
        if self.action == "list":
            return CarListSerializer
        if self.action == "retrieve":
            return CarDetailSerializer
        if self.action == "upload_image":
            return CarImageSerializer
        return CarSerializer

    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
        permission_classes=[IsAdminUser],
    )
    def upload_image(self, request, pk=None):
        """
        Custom action for uploading an image to a specific Car instance.
        Only accessible by admin users.
        """
        car = self.get_object()
        serializer = self.get_serializer(car, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
