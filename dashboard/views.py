from django.shortcuts import render
from django.views.generic import View
from rest_framework.views import APIView
from rest_framework.response import Response
from store.models import Customer, Order, Tenant
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from datetime import datetime, timedelta
from rest_framework.permissions import IsAuthenticated
from rest_framework import status


class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            tenant = request.user.tenant
        except Tenant.DoesNotExist:
            return Response(
                {"error": "No tenant associated with this user."},
                status=status.HTTP_403_FORBIDDEN,
            )

        total_customers = Customer.objects.filter(tenant=tenant).count()
        total_orders = Order.objects.filter(tenant=tenant).count()
        total_revenue = (
            Order.objects.filter(tenant=tenant).aggregate(
                total_revenue=Sum("total_price")
            )["total_revenue"]
            or 0
        )

        return Response(
            {
                "total_customers": total_customers,
                "total_orders": total_orders,
                "total_revenue": total_revenue,
            }
        )


class OrdersByDateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            tenant = request.user.tenant
        except Tenant.DoesNotExist:
            return Response(
                {"error": "No tenant associated with this user."},
                status=status.HTTP_403_FORBIDDEN,
            )

        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)

        start_date_str = request.query_params.get("start_date", None)
        end_date_str = request.query_params.get("end_date", None)

        if start_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        if end_date_str:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

        orders_by_date = (
            Order.objects.filter(
                tenant=tenant, created_at__date__range=[start_date, end_date]
            )
            .annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(order_count=Count("id"))
            .order_by("date")
        )

        return Response(orders_by_date)


class TopCustomersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            tenant = request.user.tenant
        except Tenant.DoesNotExist:
            return Response(
                {"error": "No tenant associated with this user."},
                status=status.HTTP_403_FORBIDDEN,
            )

        top_customers = (
            Customer.objects.filter(tenant=tenant)
            .annotate(total_spent=Sum("orders__total_price"))
            .order_by("-total_spent")[:5]
            .values("first_name", "last_name", "email", "total_spent")
        )

        return Response(top_customers)