import django_filters

from .models import Car


class CarFilter(django_filters.FilterSet):
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
        if value:
            return queryset.filter(inventory__gt=0)
        return queryset.filter(inventory=0)
