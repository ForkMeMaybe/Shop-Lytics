from celery import shared_task
from .utils import fetch_existing_data, subscribe_to_webhooks

@shared_task
def fetch_existing_data_task(tenant_id):
    from .models import Tenant
    try:
        tenant = Tenant.objects.get(id=tenant_id)
        fetch_existing_data(tenant)
    except Tenant.DoesNotExist:
        pass

@shared_task
def subscribe_to_webhooks_task(tenant_id):
    from .models import Tenant
    try:
        tenant = Tenant.objects.get(id=tenant_id)
        subscribe_to_webhooks(tenant)
    except Tenant.DoesNotExist:
        pass
