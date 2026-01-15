from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Rental
from .serializers import RentalCreateSerializer, RentalSerializer
from notifications.tasks import notify_new_rental


class RentalViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Rental.objects.all()
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        if self.request.user.is_staff:
            return Rental.objects.all()
        return Rental.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return RentalCreateSerializer
        return RentalSerializer

    def perform_create(self, serializer):
        rental = serializer.save()
        notify_new_rental.delay(rental.id)