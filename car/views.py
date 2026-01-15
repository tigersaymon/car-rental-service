from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.viewsets import ModelViewSet

from .filters import CarFilter
from .models import Car
from .serializers import CarSerializer


class CarViewSet(ModelViewSet):
    queryset = Car.objects.all()
    serializer_class = CarSerializer

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]

    filterset_class = CarFilter

    search_fields = ["brand", "model"]
    ordering_fields = ["daily_rate", "year"]
    ordering = ["brand"]
