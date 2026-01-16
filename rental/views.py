from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from .filters import RentalFilter
from .models import Rental
from .serializers import (
    RentalCreateSerializer,
    RentalDetailSerializer,
    RentalListSerializer,
)


class RentalViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Rental.objects.select_related("car", "user")
    permission_classes = (IsAuthenticated,)

    filter_backends = (DjangoFilterBackend,)
    filterset_class = RentalFilter

    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user

        if user.is_staff:
            return queryset
        return queryset.filter(user=user)

    def get_serializer_class(self):
        if self.action == "list":
            return RentalListSerializer
        if self.action == "retrieve":
            return RentalDetailSerializer
        if self.action == "create":
            return RentalCreateSerializer
        return RentalListSerializer
