import django_filters

from .models import Car


class CarFilter(django_filters.FilterSet):
    """
    Filters for Car queryset.

    Available filters:
    - price_min / price_max: filter by daily_rate range
    - min_year / max_year: filter by year range
    - available: True → inventory > 0, False → inventory = 0
    - brand: case-insensitive substring match
    - fuel_type: exact match
    """

    price_min = django_filters.NumberFilter(field_name="daily_rate", lookup_expr="gte")
    price_max = django_filters.NumberFilter(field_name="daily_rate", lookup_expr="lte")

    min_year = django_filters.NumberFilter(field_name="year", lookup_expr="gte")
    max_year = django_filters.NumberFilter(field_name="year", lookup_expr="lte")

    available = django_filters.BooleanFilter(method="filter_available", label="Available for rent")

    brand = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Car
        fields = ["fuel_type"]

    def filter_available(self, queryset, name, value):
        """
        Return cars with inventory > 0 if value is True, else inventory = 0.
        """
        if value:
            return queryset.filter(inventory__gt=0)
        return queryset.filter(inventory=0)
