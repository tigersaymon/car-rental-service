import django_filters

from .models import Car


class CarFilter(django_filters.FilterSet):
    """Filters for Car queryset."""

    price_min = django_filters.NumberFilter(field_name="daily_rate", lookup_expr="gte")
    price_max = django_filters.NumberFilter(field_name="daily_rate", lookup_expr="lte")

    min_year = django_filters.NumberFilter(field_name="year", lookup_expr="gte")
    max_year = django_filters.NumberFilter(field_name="year", lookup_expr="lte")

    available = django_filters.BooleanFilter(method="filter_available", label="Available for rent")

    brand = django_filters.CharFilter(lookup_expr="icontains")

    start_date = django_filters.DateFilter(method="filter_do_nothing", label="Start Date")
    end_date = django_filters.DateFilter(method="filter_do_nothing", label="End Date")

    class Meta:
        model = Car
        fields = ["fuel_type"]

    def filter_do_nothing(self, queryset, name, value):
        """Return queryset unchanged (placeholder for external filtering)."""
        return queryset

    def filter_available(self, queryset, name, value):
        """Filter cars by availability using annotation or inventory."""
        if value:
            if hasattr(queryset, "query") and "cars_available" in queryset.query.annotations:
                return queryset.filter(cars_available__gt=0)
            return queryset.filter(inventory__gt=0)

        return queryset.filter(inventory=0)
