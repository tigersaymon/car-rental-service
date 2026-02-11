import django_filters

from .models import Rental


class RentalFilter(django_filters.FilterSet):
    """
    FilterSet for the Rental model.

    Features:
    - Filters by 'status' (BOOKED, OVERDUE, etc.).
    - Filters by 'user' (ID).

    Security:
    - Automatically removes the 'user' filter for non-staff users
      to prevent enumeration or filtering of other users' data.
    """

    class Meta:
        model = Rental
        fields = ["status", "user"]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        request = self.request

        if request and not request.user.is_staff:
            del self.filters["user"]
