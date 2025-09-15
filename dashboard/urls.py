from django.urls import path
from . import views

urlpatterns = [
    path("api/stats/", views.DashboardStatsView.as_view(), name="dashboard-stats"),
    path(
        "api/orders-by-date/", views.OrdersByDateView.as_view(), name="orders-by-date"
    ),
    path("api/top-customers/", views.TopCustomersView.as_view(), name="top-customers"),
]
