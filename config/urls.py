from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/user/", include("user.urls", namespace="user")),
    path("api/", include("car.urls", namespace="car")),
    path("api/", include("rental.urls", namespace="rental")),
]
