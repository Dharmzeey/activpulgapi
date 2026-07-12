from django.urls import path

from . import views

app_name = "listings"

urlpatterns = [
    path("categories/", views.CategoryListView.as_view(), name="categories"),
    path("listings/", views.ListingListCreateView.as_view(), name="listing-list"),
    path("listings/mine/", views.MyListingsView.as_view(), name="my-listings"),
    path("listings/<slug:slug>/", views.ListingDetailView.as_view(), name="listing-detail"),
    path("listings/<slug:slug>/favorite/", views.FavoriteToggleView.as_view(), name="favorite-toggle"),
    path("favorites/", views.FavoriteListView.as_view(), name="favorites"),
    path("recommendations/", views.RecommendationsView.as_view(), name="recommendations"),
]
