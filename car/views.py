from rest_framework.viewsets import ModelViewSet

from .models import Car
from .serializers import CarSerializer


class CarViewSet(ModelViewSet):
    queryset = Car.objects.all()
    serializer_class = CarSerializer
