import django_filters

from .models import Rental


class RentalFilter(django_filters.FilterSet):
    """
    FilterSet for the Rental model.

    Dynamically hides the 'user' filter for non-staff users to prevent
    them from filtering rentals by other users.
    """

    class Meta:
        model = Rental
        fields = ["status", "user"]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        request = self.request

        if request and not request.user.is_staff:
            del self.filters["user"]
