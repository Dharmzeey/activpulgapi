import django_filters

from .models import Listing


class ListingFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(field_name="category__slug")
    school = django_filters.CharFilter(field_name="school__slug")
    condition = django_filters.CharFilter(field_name="condition")
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")

    class Meta:
        model = Listing
        fields = ["category", "school", "condition", "min_price", "max_price"]
