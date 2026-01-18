from django.db.models import Count, F, Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiTypes,
    extend_schema,
    extend_schema_view,
)
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
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


@extend_schema_view(
    list=extend_schema(
        summary="Get list of cars",
        description=(
            "Retrieve a list of cars. Supports filtering by brand, price, year, and availability. "
            "If `start_date` and `end_date` are provided, the system filters out cars "
            "that are fully booked for that period."
        ),
        parameters=[
            OpenApiParameter(
                name="start_date",
                description="Filter available cars starting from this date (YYYY-MM-DD)",
                required=False,
                type=OpenApiTypes.DATE,
            ),
            OpenApiParameter(
                name="end_date",
                description="Filter available cars until this date (YYYY-MM-DD)",
                required=False,
                type=OpenApiTypes.DATE,
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Get car details",
        description="Retrieve detailed information about a specific car, including description and full specs.",
    ),
    create=extend_schema(
        summary="Create a new car",
        description="Create a car with an optional image upload.",
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "brand": {"type": "string"},
                    "model": {"type": "string"},
                    "year": {"type": "integer"},
                    "fuel_type": {"type": "string"},
                    "daily_rate": {"type": "number"},
                    "inventory": {"type": "integer"},
                    "image": {"type": "string", "format": "binary"},
                },
                "required": ["brand", "model", "year", "daily_rate", "inventory"],
            }
        },
    ),
    update=extend_schema(summary="Update car details (Admin only)"),
    partial_update=extend_schema(summary="Partially update car details (Admin only)"),
    destroy=extend_schema(summary="Delete a car (Admin only)"),
)
class CarViewSet(ModelViewSet):
    """
    Manage Car objects: CRUD, filtering, search, ordering, and image upload.
    """

    queryset = Car.objects.all()
    serializer_class = CarSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CarFilter
    search_fields = ["brand", "model"]
    ordering_fields = ["daily_rate", "year"]
    ordering = ["brand"]

    def get_queryset(self):
        """
        Annotate queryset with cars_available based on optional date range.
        """
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

    @extend_schema(
        summary="Upload car image",
        description="Upload an image file for a specific car. Only accessible by admins.",
        request=CarImageSerializer,
        responses={
            200: CarImageSerializer,
            400: "Bad Request (Invalid image or data)",
        },
    )
    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
        permission_classes=[IsAdminUser],
    )
    def upload_image(self, request, pk=None):
        car = self.get_object()
        serializer = self.get_serializer(car, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
