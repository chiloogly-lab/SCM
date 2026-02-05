from celery import shared_task

@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 3, "countdown": 10})
def sla_monitor(self):
    print("SLA monitor running")
