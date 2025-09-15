from django.urls import path
from . import views

urlpatterns = [
    path('tenants/', views.TenantListCreateView.as_view(), name='tenant-list-create'),
    path('tenants/<int:pk>/', views.TenantDetailView.as_view(), name='tenant-detail'),
    path('customers/', views.CustomerListCreateView.as_view(), name='customer-list-create'),
    path('customers/<int:pk>/', views.CustomerDetailView.as_view(), name='customer-detail'),
    path('products/', views.ProductListCreateView.as_view(), name='product-list-create'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('orders/', views.OrderListCreateView.as_view(), name='order-list-create'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('custom-events/', views.CustomEventListCreateView.as_view(), name='custom-event-list-create'),
]
