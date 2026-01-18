from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from user.views import (
    CreateUserView,
    GoogleAuthExchangeCodeView,
    GoogleAuthRedirectView,
    ManageUserView,
)


urlpatterns = [
    path("", CreateUserView.as_view(), name="create"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", ManageUserView.as_view(), name="manage"),
    path("auth/google/", GoogleAuthRedirectView.as_view(), name="google-auth-redirect"),
    path("auth/google/exchange-code/", GoogleAuthExchangeCodeView.as_view(), name="google_exchange_code"),
]


app_name = "user"
