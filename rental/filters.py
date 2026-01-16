import django_filters

from .models import Rental


class RentalFilter(django_filters.FilterSet):
    class Meta:
        model = Rental
        fields = ["status", "user"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.request

        if request and not request.user.is_staff:
            del self.filters["user"]
