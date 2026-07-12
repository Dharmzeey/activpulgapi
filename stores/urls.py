from django.urls import path

from . import views

app_name = "stores"

urlpatterns = [
    path("stores/", views.StoreListView.as_view(), name="store-list"),
    path("stores/create/", views.StoreCreateView.as_view(), name="store-create"),
    path("stores/mine/", views.MyStoreView.as_view(), name="my-store"),
    path("stores/<slug:slug>/", views.StoreDetailView.as_view(), name="store-detail"),
]
