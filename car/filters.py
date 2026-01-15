import django_filters

from .models import Car


class CarFilter(django_filters.FilterSet):
    price_min = django_filters.NumberFilter(field_name="daily_rate", lookup_expr="gte")
    price_max = django_filters.NumberFilter(field_name="daily_rate", lookup_expr="lte")

    year_from = django_filters.NumberFilter(field_name="year", lookup_expr="gte")
    year_to = django_filters.NumberFilter(field_name="year", lookup_expr="lte")

    available = django_filters.BooleanFilter(method="filter_available", label="Available for rent")

    class Meta:
        model = Car
        fields = [
            "brand",
            "fuel_type",
        ]

    def filter_available(self, queryset, name, value):
        if value:
            return queryset.filter(inventory__gt=0)
        return queryset.filter(inventory=0)
