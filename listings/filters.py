import django_filters

from .models import Listing


class ListingFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(field_name="category__slug")
    school = django_filters.CharFilter(field_name="school__slug")
    store = django_filters.CharFilter(method="filter_store")
    condition = django_filters.CharFilter(field_name="condition")
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")

    def filter_store(self, queryset, name, value):
        return queryset.filter(
            seller__store__slug=value, seller__store__is_active=True
        )

    class Meta:
        model = Listing
        fields = ["category", "school", "store", "condition", "min_price", "max_price"]
