from functools import wraps

from . import conf
from .models import TranslationRequest

if conf.TRANSLATIONS_USE_CELERY:
    from aldryn_celery import celery_app as app

    task_decorator = app.task

else:
    def fake_task(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            func(*args, **kwargs)

        wrapped.delay = wrapped
        return wrapped

    task_decorator = fake_task


@task_decorator
def prepare_translation_bulk_request(translation_request_id):
    translation_request = TranslationRequest.objects.get(id=translation_request_id)
    translation_request.export_content_from_cms()
    translation_request.get_quote_from_provider()
