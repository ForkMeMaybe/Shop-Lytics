from django.urls import path
from . import views

urlpatterns = [
    path("send_otp/", views.send_otp, name="send_otp"),
    path("verify_otp/", views.verify_otp, name="verify_otp"),
    path('auth/shopify/', views.shopify_auth, name='shopify_auth'),
    path('auth/shopify/callback/', views.shopify_callback, name='shopify_callback'),
]
