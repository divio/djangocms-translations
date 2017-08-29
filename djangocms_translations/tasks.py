from aldryn_celery import celery_app as app


@app.task
def get_quote_from_provider(request):
    return request.get_quote_from_provider()
