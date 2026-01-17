from django.db.models import Count, F, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from rental.models import Rental

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

    def get_queryset(self):
        queryset = self.queryset

        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        if start_date and end_date:
            queryset = (
                queryset.annotate(
                    count_booked_rentals=Count(
                        "rentals",
                        filter=Q(
                            rentals__status=Rental.Status.BOOKED,
                            rentals__start_date__lte=end_date,
                            rentals__end_date__gte=start_date,
                        ),
                    )
                )
                .annotate(cars_available=F("inventory") - F("count_booked_rentals"))
                .filter(cars_available__gt=0)
            )
        else:
            queryset = queryset.annotate(cars_available=F("inventory"))

        return queryset

    def get_serializer_class(self):
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
